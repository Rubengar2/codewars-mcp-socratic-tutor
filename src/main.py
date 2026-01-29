"""CodeWars MCP Server for Python Practice.

This module provides an MCP (Model Context Protocol) server for managing
CodeWars kata exercises, including importing, tracking progress, and setting
up practice environments.
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from mcp.server.fastmcp import FastMCP

from api_client import fetch_kata_details, fetch_user_completed

mcp = FastMCP("Codewars Tutor")

BASE_DIR = Path(__file__).parent.parent
INDEX_PATH = BASE_DIR / "data" / "katas_index.json"
CONFIG_PATH = BASE_DIR / "data" / "config.json"
HISTORY_PATH = BASE_DIR / "data" / "user_history.json"
EXERCISES_DIR = BASE_DIR / "exercises"



def sanitize_folder_name(name: str) -> str:
    """Clean kata name for folder usage.
    
    Converts kata names to valid folder names by removing special characters
    and converting to lowercase with underscores.
    
    Args:
        name: The kata name to sanitize.
        
    Returns:
        A sanitized folder name in snake_case format.
        
    Examples:
        >>> sanitize_folder_name("Valid Braces")
        'valid_braces'
        >>> sanitize_folder_name("Stop gninnipS My sdroW!")
        'stop_gninnips_my_sdrow'
    """
    cleaned_name = "".join(
        char if char.isalnum() or char in (' ', '-', '_') else '' 
        for char in name
    ).strip()
    return cleaned_name.replace(' ', '_').lower()


def generate_function_name(name: str) -> str:
    """Convert kata title to a valid Python function name.
    
    Transforms kata titles into snake_case Python function names,
    handling special characters and ensuring valid Python identifiers.
    
    Args:
        name: The kata title to convert.
        
    Returns:
        A valid Python function name in snake_case format.
        
    Examples:
        >>> generate_function_name("Valid Braces")
        'valid_braces'
        >>> generate_function_name("123 Numbers")
        'kata_123_numbers'
    """
    words = re.split(r'[^a-zA-Z0-9]+', name)
    snake_case_name = "_".join(word.lower() for word in words if word)
    
    if snake_case_name and snake_case_name[0].isdigit():
        snake_case_name = f"kata_{snake_case_name}"
        
    return snake_case_name


def load_config() -> Optional[Dict[str, Any]]:
    """Load configuration from config file.
    
    Returns:
        Dictionary containing configuration data if file exists, None otherwise.
    """
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    return None


def sync_history_internal(username: str) -> List[str]:
    """Synchronize user history from CodeWars API.
    
    Internal function to fetch and cache user's completed katas without
    generating user-facing messages.
    
    Args:
        username: CodeWars username to sync history for.
        
    Returns:
        List of kata IDs that the user has completed.
    """
    try:
        completed_katas_data = fetch_user_completed(username, page=0)
        
        if "error" in completed_katas_data:
            return []
            
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as history_file:
            json.dump(completed_katas_data, history_file, indent=2)
            
        return [kata["id"] for kata in completed_katas_data]
        
    except (IOError, KeyError, TypeError) as e:
        return []



@mcp.tool()
def update_progress(username: str = None) -> str:
    """Force update of local history by querying CodeWars API.
    
    Use this tool when the user reports completing an exercise on the
    CodeWars website to refresh their local progress tracking.
    
    Args:
        username: CodeWars username. If None, uses configured default.
        
    Returns:
        Status message indicating success or failure of the sync operation.
    """
    try:
        config = load_config()
        active_username = username or (config.get("codewars_username") if config else None)
        
        if not active_username:
            return (
                "❌ Error: No se encontró configuración de usuario. "
                "Por favor ejecuta 'setup.py' primero."
            )

        completed_katas_data = fetch_user_completed(active_username, page=0)
        
        if "error" in completed_katas_data:
            return (
                f"❌ Error conectando con CodeWars: "
                f"{completed_katas_data['error']}"
            )

        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as history_file:
            json.dump(completed_katas_data, history_file, indent=2)
            
        kata_count = len(completed_katas_data)
        return (
            f"✅ Sincronización exitosa. Historial local actualizado "
            f"con {kata_count} ejercicios recientes."
        )
        
    except IOError as e:
        return f"❌ Error de archivo al guardar historial: {e}"
    except Exception as e:
        return f"❌ Error crítico al actualizar: {e}"


@mcp.tool()
def import_kata(url_or_id: str) -> str:
    """Import a specific kata by URL or ID.
    
    Allows importing exercises that may not be in the local index by
    fetching them directly from the CodeWars API.
    
    Args:
        url_or_id: CodeWars kata URL or kata ID.
        
    Returns:
        Status message with exercise setup details or error information.
        
    Examples:
        >>> import_kata("https://www.codewars.com/kata/5277c8a221e209d3f6000b56")
        >>> import_kata("5277c8a221e209d3f6000b56")
    """
    try:
        kata_id_match = re.search(r'kata/([a-f0-9]+)|([a-f0-9]{24})', url_or_id)
        kata_id = (
            kata_id_match.group(1) or kata_id_match.group(2) 
            if kata_id_match 
            else url_or_id.strip()
        )

        kata_details = fetch_kata_details(kata_id)
        
        if "error" in kata_details:
            return (
                f"❌ No pude encontrar el ejercicio '{kata_id}'. "
                "Verifica el ID o la URL."
            )

        return setup_exercise_environment(kata_details, origin="Importación Manual")
        
    except re.error as e:
        return f"❌ Error al procesar la URL/ID: {e}"
    except Exception as e:
        return f"❌ Error al importar: {e}"


@mcp.tool()
def practice_python() -> str:
    """Select and set up a random uncompleted kata for practice.
    
    Main workflow:
    1. Load local index and user configuration
    2. Sync user's completed katas from CodeWars
    3. Filter out completed exercises
    4. Select a random available kata
    5. Lazy load full kata details from API
    6. Create exercise folder and starter files
    
    Returns:
        Status message with exercise details and file locations.
    """
    try:
        config = load_config()
        if not config:
            return (
                "❌ Error: No se encontró configuración. "
                "Por favor ejecuta setup.py primero."
            )
            
        username = config.get("codewars_username")
        if not username:
            return (
                "❌ Error: No se encontró username en la configuración. "
                "Por favor ejecuta setup.py primero."
            )
        
        completed_kata_ids = set(sync_history_internal(username))
        
        if not completed_kata_ids and HISTORY_PATH.exists():
            try:
                cached_history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
                completed_kata_ids = {kata["id"] for kata in cached_history}
            except (json.JSONDecodeError, KeyError) as e:
                return f"❌ Error al leer historial cacheado: {e}"

        if not INDEX_PATH.exists():
            return (
                "⚠️ Error: No encuentro 'data/katas_index.json'. "
                "Por favor ejecuta 'python src/indexer.py' para generar "
                "la base de datos de ejercicios."
            )
        
        try:
            full_kata_index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return f"❌ Error al leer índice de katas: {e}"

        available_katas = [
            kata for kata in full_kata_index 
            if kata["id"] not in completed_kata_ids
        ]
        
        if not available_katas:
            return (
                "🎉 ¡Increíble! Has completado todos los ejercicios indexados. "
                "Intenta ejecutar 'src/indexer.py' de nuevo para buscar más, "
                "o usa 'import_kata' con una URL específica."
            )

        selected_kata_index = random.choice(available_katas)
        
        kata_details = fetch_kata_details(selected_kata_index["id"])
        
        if "error" in kata_details:
            return (
                f"❌ Hubo un error descargando el contenido del ejercicio "
                f"'{selected_kata_index['name']}': {kata_details['error']}"
            )

        return setup_exercise_environment(
            kata_details, 
            origin="Recomendación Automática"
        )

    except KeyError as e:
        return f"❌ Error: Falta campo requerido en los datos: {e}"
    except Exception as e:
        return f"❌ Error inesperado en practice_python: {e}"



def setup_exercise_environment(kata_details: Dict[str, Any], origin: str) -> str:
    """Create exercise folder structure and starter files.
    
    Sets up a complete exercise environment including README with kata
    description and a solution.py file with function template.
    
    Args:
        kata_details: Dictionary containing kata information from API.
        origin: Description of how the kata was selected (for user feedback).
        
    Returns:
        Formatted message with exercise setup details and file locations.
        
    Raises:
        IOError: If unable to create files or directories.
        KeyError: If required fields missing from kata_details.
    """
    try:
        rank_info = kata_details.get('rank', {})
        rank_name = rank_info.get('name', 'N/A').replace(' ', '')
        folder_slug = sanitize_folder_name(kata_details['name'])
        
        folder_name = f"{rank_name}_python_{folder_slug}"
        exercise_folder_path = EXERCISES_DIR / folder_name
        exercise_folder_path.mkdir(parents=True, exist_ok=True)
        
        function_name = generate_function_name(kata_details['name'])

        readme_content = f"""# {kata_details['name']} [{rank_name}]

**URL:** {kata_details['url']}

## Descripción
{kata_details['description']}
"""
        readme_path = exercise_folder_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        
        solution_file_path = exercise_folder_path / "solution.py"
        if not solution_file_path.exists():
            solution_template = f'''"""
Kata: {kata_details['name']}
Nivel: {rank_name}
URL: {kata_details['url']}
"""

def {function_name}(args):
    """Implement kata solution here.
    
    Note: Verify on CodeWars if the function name '{function_name}' is correct
    (sometimes they use camelCase instead of snake_case).
    
    Args:
        args: Replace with actual parameter names and types.
        
    Returns:
        Replace with actual return type.
    """
    pass


if __name__ == "__main__":
    print(f"Testing {{__name__.split('.')[0]}}...")
    # Add test cases here
'''
            solution_file_path.write_text(solution_template, encoding="utf-8")

        return f"""
🚀 EJERCICIO LISTO ({origin})

He preparado: **{kata_details['name']}**

📂 Carpeta: `{exercise_folder_path}`
📄 Archivo: `solution.py` con la función `def {function_name}(...):`

Dile al usuario que abra esa carpeta y comience a leer el README.
"""
    
    except KeyError as e:
        return f"❌ Error: Falta campo requerido en kata_details: {e}"
    except IOError as e:
        return f"❌ Error al crear archivos del ejercicio: {e}"
    except Exception as e:
        return f"❌ Error inesperado al configurar ejercicio: {e}"


if __name__ == "__main__":
    mcp.run()