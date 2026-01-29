"""CodeWars API Client Module.

Provides robust HTTP client functions for interacting with the CodeWars API v1.
Includes proper error handling, timeouts, and type hints for production use.

API Documentation: https://dev.codewars.com
"""

from typing import Dict, List, Any, Union
import httpx


BASE_URL = "https://www.codewars.com/api/v1"
DEFAULT_TIMEOUT = 10.0  # seconds
MAX_RETRIES = 3


class CodeWarsAPIError(Exception):
    """Custom exception for CodeWars API errors."""
    pass


def fetch_codewars_user(username: str) -> Dict[str, Any]:
    """Fetch user profile information from CodeWars API.
    
    Retrieves comprehensive user data including rank, honor points, skills,
    and other profile information.
    
    Args:
        username: CodeWars username to fetch.
        
    Returns:
        Dictionary containing user profile data with structure:
        {
            "username": str,
            "name": str,
            "honor": int,
            "clan": str,
            "leaderboardPosition": int,
            "skills": List[str],
            "ranks": {
                "overall": {"rank": int, "name": str, "color": str, "score": int},
                "languages": {...}
            },
            ...
        }
        Or error dictionary: {"error": str} if user not found or request fails.
        
    Examples:
        >>> user_data = fetch_codewars_user("johndoe")
        >>> print(user_data["honor"])
        1234
    """
    url = f"{BASE_URL}/users/{username}"
    
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url)
            
            if response.status_code == 404:
                return {"error": f"El usuario '{username}' no existe en CodeWars."}
            
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        return {
            "error": f"Timeout al conectar con CodeWars API para usuario '{username}'. "
            f"Intenta nuevamente."
        }
    except httpx.ConnectError:
        return {
            "error": "Error de conexión. Verifica tu conexión a internet."
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Error HTTP {e.response.status_code}: {e.response.text}"
        }
    except Exception as e:
        return {
            "error": f"Error inesperado al obtener usuario: {e}"
        }


def fetch_user_completed(username: str, page: int = 0) -> List[Dict[str, Any]]:
    """Fetch list of completed katas for a user.
    
    Retrieves paginated list of katas (challenges) that the user has completed.
    The CodeWars API returns 200 results per page.
    
    Args:
        username: CodeWars username.
        page: Page number for pagination (0-indexed). Defaults to 0.
        
    Returns:
        List of dictionaries, each containing completed kata information:
        [
            {
                "id": str,
                "name": str,
                "slug": str,
                "completedAt": str (ISO datetime),
                "completedLanguages": List[str]
            },
            ...
        ]
        Or list with single error dictionary: [{"error": str}] on failure.
        
    Examples:
        >>> completed = fetch_user_completed("johndoe", page=0)
        >>> print(len(completed))
        200
    """
    url = f"{BASE_URL}/users/{username}/code-challenges/completed?page={page}"
    
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url)
            
            if response.status_code == 404:
                return [{"error": f"Usuario '{username}' no encontrado."}]
            
            response.raise_for_status()
            json_data = response.json()
            return json_data.get("data", [])
            
    except httpx.TimeoutException:
        return [{
            "error": f"Timeout al obtener katas completados de '{username}'. "
            f"Intenta nuevamente."
        }]
    except httpx.ConnectError:
        return [{
            "error": "Error de conexión. Verifica tu conexión a internet."
        }]
    except httpx.HTTPStatusError as e:
        return [{
            "error": f"Error HTTP {e.response.status_code}: {e.response.text}"
        }]
    except (KeyError, ValueError) as e:
        return [{
            "error": f"Error al parsear respuesta de la API: {e}"
        }]
    except Exception as e:
        return [{
            "error": f"Error inesperado al obtener katas completados: {e}"
        }]


def fetch_kata_details(kata_id_or_slug: str) -> Dict[str, Any]:
    """Fetch complete details for a specific kata.
    
    Retrieves comprehensive information about a kata including description,
    rank, tags, statistics, and creator information.
    
    Args:
        kata_id_or_slug: Kata ID (24-char hex) or slug (URL-friendly name).
        
    Returns:
        Dictionary containing kata details with structure:
        {
            "id": str,
            "name": str,
            "slug": str,
            "url": str,
            "category": str,
            "description": str,
            "tags": List[str],
            "languages": List[str],
            "rank": {
                "id": int,
                "name": str,
                "color": str
            },
            "createdBy": {
                "username": str,
                "url": str
            },
            "totalAttempts": int,
            "totalCompleted": int,
            "totalStars": int,
            ...
        }
        Or error dictionary: {"error": str} if kata not found or request fails.
        
    Examples:
        >>> kata = fetch_kata_details("5277c8a221e209d3f6000b56")
        >>> print(kata["name"])
        'Valid Braces'
    """
    url = f"{BASE_URL}/code-challenges/{kata_id_or_slug}"
    
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url)
            
            if response.status_code == 404:
                return {
                    "error": f"Ejercicio '{kata_id_or_slug}' no encontrado."
                }
            
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        return {
            "error": f"Timeout al obtener detalles del kata '{kata_id_or_slug}'. "
            f"Intenta nuevamente."
        }
    except httpx.ConnectError:
        return {
            "error": "Error de conexión. Verifica tu conexión a internet."
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Error HTTP {e.response.status_code}: {e.response.text}"
        }
    except Exception as e:
        return {
            "error": f"Error inesperado al obtener detalles del kata: {e}"
        }