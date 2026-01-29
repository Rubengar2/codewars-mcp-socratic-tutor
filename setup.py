"""CodeWars MCP Setup Script.

Interactive setup wizard for configuring the CodeWars MCP server,
including user authentication, data synchronization, and VS Code integration.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any


project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root / "src"))

try:
    from api_client import fetch_codewars_user, fetch_user_completed
except ImportError as e:
    print("❌ Error crítico: No se pudo importar api_client.py")
    print(f"   Detalle: {e}")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class SetupWizard:
    """Interactive setup wizard for CodeWars MCP configuration."""
    
    def __init__(self):
        """Initialize setup wizard with project paths."""
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.vscode_dir = self.project_root / ".vscode"
        self.index_file = self.data_dir / "katas_index.json"
        self.config_file = self.data_dir / "config.json"
        self.history_file = self.data_dir / "user_history.json"
        
    def print_header(self) -> None:
        """Display welcome banner."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}🚀 CodeWars MCP - Asistente de Instalación{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        
    def print_success(self, message: str) -> None:
        """Print success message in green."""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
        
    def print_error(self, message: str) -> None:
        """Print error message in red."""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
        
    def print_warning(self, message: str) -> None:
        """Print warning message in yellow."""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")
        
    def print_info(self, message: str) -> None:
        """Print info message in cyan."""
        print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")
        
    def ensure_directories(self) -> bool:
        """Create required directories if they don't exist.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.print_success(f"Directorio de datos: {self.data_dir}")
            return True
        except PermissionError:
            self.print_error(
                f"Sin permisos para crear directorio: {self.data_dir}"
            )
            return False
        except Exception as e:
            self.print_error(f"Error al crear directorios: {e}")
            return False
            
    def verify_index(self) -> bool:
        """Verify kata index file exists and is valid.
        
        Returns:
            True if index exists and is valid, False otherwise.
        """
        if not self.index_file.exists():
            self.print_warning(
                "No se encontró 'katas_index.json' en el directorio data/"
            )
            self.print_info(
                "El índice se generará automáticamente o puedes ejecutar "
                "'python src/indexer.py'"
            )
            return False
            
        try:
            index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
            kata_count = len(index_data)
            self.print_success(
                f"Base de datos cargada: {kata_count} ejercicios disponibles"
            )
            return True
        except json.JSONDecodeError as e:
            self.print_error(f"El archivo katas_index.json está corrupto: {e}")
            return False
        except Exception as e:
            self.print_error(f"Error al leer katas_index.json: {e}")
            return False
            
    def configure_user(self) -> Optional[str]:
        """Interactive user configuration with API validation.
        
        Returns:
            Username if successful, None otherwise.
        """
        print(f"\n{Colors.BOLD}{'─'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Paso 1: Configuración de Usuario{Colors.RESET}")
        print(f"{Colors.BOLD}{'─'*60}{Colors.RESET}\n")
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            username = input(f"{Colors.CYAN}👤 Ingresa tu usuario de CodeWars: {Colors.RESET}").strip()
            
            if not username:
                self.print_warning("El nombre de usuario no puede estar vacío")
                continue
                
            attempt += 1
            print(f"{Colors.CYAN}⏳ Validando usuario '{username}'...{Colors.RESET}")
            
            user_data = fetch_codewars_user(username)
            
            if "error" in user_data:
                self.print_error(user_data["error"])
                
                if "conexión" in user_data["error"].lower():
                    self.print_warning(
                        "Verifica tu conexión a internet e intenta nuevamente"
                    )
                    retry = input(f"{Colors.CYAN}¿Reintentar? (s/n): {Colors.RESET}").lower()
                    if retry != 's':
                        return None
                    attempt -= 1
                    continue
                    
                remaining = max_attempts - attempt
                if remaining > 0:
                    self.print_info(f"Intentos restantes: {remaining}")
                continue
                
            self.print_success(f"Usuario validado: {username}")
            
            if "honor" in user_data:
                print(f"   Honor: {user_data['honor']}")
            if "ranks" in user_data and "overall" in user_data["ranks"]:
                rank = user_data["ranks"]["overall"].get("name", "N/A")
                print(f"   Rango: {rank}")
                
            return username
            
        self.print_error("Máximo de intentos alcanzado")
        return None
        
    def save_user_config(self, username: str) -> bool:
        """Save user configuration to file.
        
        Args:
            username: CodeWars username to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            config_data = {"codewars_username": username}
            self.config_file.write_text(
                json.dumps(config_data, indent=2),
                encoding="utf-8"
            )
            self.print_success(f"Configuración guardada en {self.config_file}")
            return True
        except PermissionError:
            self.print_error(f"Sin permisos para escribir en {self.config_file}")
            return False
        except Exception as e:
            self.print_error(f"Error al guardar configuración: {e}")
            return False
            
    def sync_user_history(self, username: str) -> bool:
        """Synchronize user's completed katas from CodeWars API.
        
        Args:
            username: CodeWars username.
            
        Returns:
            True if successful, False otherwise.
        """
        print(f"\n{Colors.CYAN}⏳ Sincronizando historial de katas completados...{Colors.RESET}")
        
        history_data = fetch_user_completed(username, page=0)
        
        if history_data and "error" in history_data[0]:
            self.print_error(history_data[0]["error"])
            self.print_warning("Se continuará sin historial sincronizado")
            return False
            
        try:
            self.history_file.write_text(
                json.dumps(history_data, indent=2),
                encoding="utf-8"
            )
            completed_count = len(history_data)
            self.print_success(
                f"Historial sincronizado: {completed_count} katas completados"
            )
            return True
        except Exception as e:
            self.print_error(f"Error al guardar historial: {e}")
            return False
            
    def configure_vscode(self) -> bool:
        """Configure VS Code MCP server settings.
        
        Returns:
            True if successful, False otherwise.
        """
        print(f"\n{Colors.BOLD}{'─'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Paso 2: Configuración de VS Code{Colors.RESET}")
        print(f"{Colors.BOLD}{'─'*60}{Colors.RESET}\n")
        
        python_path = self.project_root / "venv" / "bin" / "python"
        
        if not python_path.exists():
            self.print_warning(
                f"No se encontró Python en: {python_path}"
            )
            python_path = Path(sys.executable)
            self.print_info(f"Usando Python del sistema: {python_path}")
            
        mcp_config = {
            "mcp.servers": {
                "codewars-tutor": {
                    "command": str(python_path),
                    "args": [str(self.project_root / "src" / "main.py")],
                    "env": {"PYTHONUNBUFFERED": "1"},
                    "disabled": False,
                    "alwaysAllow": []
                }
            }
        }
        
        try:
            self.vscode_dir.mkdir(parents=True, exist_ok=True)
            settings_file = self.vscode_dir / "settings.json"
            
            settings_file.write_text(
                json.dumps(mcp_config, indent=2),
                encoding="utf-8"
            )
            self.print_success(f"VS Code configurado: {settings_file}")
            return True
        except PermissionError:
            self.print_error(f"Sin permisos para escribir en {self.vscode_dir}")
            return False
        except Exception as e:
            self.print_error(f"Error al configurar VS Code: {e}")
            return False
            
    def print_next_steps(self) -> None:
        """Display post-installation instructions."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}✨ INSTALACIÓN COMPLETADA ✨{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}Próximos pasos:{Colors.RESET}")
        print(f"  1. {Colors.CYAN}Reinicia VS Code{Colors.RESET}")
        print(f"  2. {Colors.CYAN}Abre GitHub Copilot Chat{Colors.RESET}")
        print(f"  3. {Colors.CYAN}Escribe: '@codewars-tutor dame un ejercicio'{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}Nota:{Colors.RESET} Si tienes problemas, verifica:")
        print(f"  • Que tienes instalada la extensión de GitHub Copilot")
        print(f"  • Que MCP está habilitado en tu configuración de VS Code\n")
        
    def run(self) -> int:
        """Execute the complete setup wizard.
        
        Returns:
            Exit code (0 for success, 1 for failure).
        """
        self.print_header()
        
        if not self.ensure_directories():
            return 1
            
        self.verify_index()
        
        username = self.configure_user()
        if not username:
            self.print_error("Configuración de usuario cancelada o fallida")
            return 1
            
        if not self.save_user_config(username):
            return 1
            
        self.sync_user_history(username)
        
        if not self.configure_vscode():
            self.print_warning(
                "Configuración de VS Code falló, pero puedes configurarlo manualmente"
            )
            
        self.print_next_steps()
        return 0


def main() -> int:
    """Main entry point for setup script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        wizard = SetupWizard()
        return wizard.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Instalación cancelada por el usuario{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())