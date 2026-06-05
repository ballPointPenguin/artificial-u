"""Modèles d'invites pour les départements (version française)."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    departments_to_xml,
    faculties_to_xml,
    partial_department_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

DEPARTMENT_XML_STRUCTURE = """
<output>
  <department>
    <name>[GÉNÉRER]</name>
    <code>[GÉNÉRER]</code>
    <faculty>[GÉNÉRER]</faculty>
    <description>[GÉNÉRER]</description>
  </department>
</output>
"""

DEPARTMENT_PROMPT = PromptTemplate(
    template=f"""
Générez un nouveau profil de département en respectant cette structure XML :
{DEPARTMENT_XML_STRUCTURE}

Instructions :
- Tous les champs (avec [GÉNÉRER]) doivent être renseignés avec des valeurs générées.
- Assurez-vous que <name> et <code> soient uniques par rapport à ceux listés sous
  <existing_departments> (vérification insensible à la casse).
- <code> doit être une abréviation courte et mémorable (2 à 8 lettres majuscules).
- <faculty> DOIT être sélectionnée dans la liste <existing_faculties> ci-dessous.
  Vous ne pouvez PAS créer de nouvelles facultés — choisissez uniquement parmi les options existantes.
  Choisissez la faculté la plus appropriée en fonction de l'orientation du département.
  Utilisez le nom exact de la faculté tel qu'il apparaît dans la liste.
- <description> doit être claire, concise et informative sur les domaines d'expertise du département.

Après avoir généré le profil, vérifiez que <name> et <code> sont uniques, que <faculty>
correspond exactement à l'une des facultés existantes (sensible à la casse), et que tous
les champs satisfont aux exigences. En cas d'échec de validation, corrigez et régénérez
la sortie. Rappel : vous ne pouvez que sélectionner parmi les facultés existantes, jamais
en créer de nouvelles.
{{existing_departments_xml}}

{{existing_faculties_xml}}

Informations partielles sur le département :
{{partial_department_xml}}

{{freeform_prompt_text}}

Exigences de formatage et de sortie :
- Ne produisez que le bloc XML encadré dans des balises <output>,
  contenant un unique élément <department> tel qu'indiqué.
- Aucun texte, note ou balisage en dehors du bloc <output> n'est autorisé.
""",
    required_vars=[
        "existing_departments_xml",
        "existing_faculties_xml",
        "partial_department_xml",
    ],
)


def get_department_prompt(
    existing_departments: Optional[List[str]] = None,
    existing_faculties: Optional[List[Dict[str, Any]]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Génère une invite de département à partir des données fournies.

    Args:
        existing_departments: Liste des départements existants pour le contexte.
        existing_faculties: Liste des facultés existantes pour la sélection.
        partial_attributes: Dictionnaire optionnel d'attributs connus pour guider la génération.
        freeform_prompt: Texte libre optionnel pour des orientations supplémentaires.

    Returns:
        Chaîne d'invite formatée.
    """
    existing_departments_xml_str = departments_to_xml(existing_departments or [])
    existing_faculties_xml_str = faculties_to_xml(existing_faculties or [])
    partial_department_xml_str = partial_department_to_xml(partial_attributes or {})

    prompt_text = f"Indications supplémentaires :\n{freeform_prompt}\n" if freeform_prompt else ""

    try:
        return DEPARTMENT_PROMPT.format(
            existing_departments_xml=existing_departments_xml_str,
            existing_faculties_xml=existing_faculties_xml_str,
            partial_department_xml=partial_department_xml_str,
            freeform_prompt_text=prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Erreur lors du formatage de DEPARTMENT_PROMPT : {e}")
