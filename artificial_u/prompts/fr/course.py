"""Modèles d'invites pour les cours (version française)."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    connected_courses_to_xml,
    courses_to_xml,
    department_to_xml,
    partial_course_to_xml,
    professor_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

COURSE_XML_STRUCTURE = """<course>
  <code>[Code du cours]</code>
  <title>[Intitulé du cours]</title>
  <description>[Description du cours]</description>
  <level>[Niveau du cours : "Licence" ou "Master"]</level>
  <lectures_per_week>[Nombre de séances par semaine]</lectures_per_week>
  <total_weeks>[Nombre total de semaines]</total_weeks>
</course>"""

EXAMPLE_COURSE_1 = """<course>
  <code>INF101</code>
  <title>Introduction à l'Informatique</title>
  <description>Une introduction accessible aux principes fondamentaux de l'informatique,
  à la programmation et à la pensée computationnelle.</description>
  <level>Licence</level>
  <lectures_per_week>1</lectures_per_week>
  <total_weeks>12</total_weeks>
</course>"""

EXAMPLE_COURSE_2 = """<course>
  <code>HIST220</code>
  <title>L'Europe médiévale</title>
  <description>Une exploration de l'histoire européenne de la chute de Rome à la Renaissance,
  examinant les évolutions sociales, politiques et culturelles.</description>
  <level>Licence</level>
  <lectures_per_week>2</lectures_per_week>
  <total_weeks>10</total_weeks>
</course>"""

COURSE_PROMPT = PromptTemplate(
    template=f"""
Générez les détails d'un cours académique au format XML.
Utilisez la structure ci-dessous ; remplissez tous les espaces réservés avec les valeurs
fournies ou des valeurs générées si marquées [GÉNÉRER].

Structure XML :
{COURSE_XML_STRUCTURE}

Consignes :
- Pour le niveau : choisissez "Licence" ou "Master" en fonction de la complexité du cours
  et du public cible.
- Pour lectures_per_week :
  - 1 à 2 séances par semaine convient à la plupart des cours
  - 3 séances par semaine pour une couverture avancée et approfondie
  - Choisissez 1, 2 ou 3 séances par semaine (pas plus)
  - Tenez compte du niveau du cours, de la complexité du sujet et du nombre total de semaines.

Cours existants (pour le contexte et éviter les répétitions) :
{{existing_courses_xml}}

Cours liés (prérequis ou séquences explicites — alignez-vous avec eux) :
{{connected_courses_xml}}

Informations sur le département :
{{department_xml}}

Informations sur le professeur :
{{professor_xml}}

Informations partielles sur le cours :
{{partial_course_xml}}

{{freeform_prompt_text}}

Exemples de cours correctement formatés :
Exemple 1 :
{EXAMPLE_COURSE_1}

Exemple 2 :
{EXAMPLE_COURSE_2}

Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <course>.
""",
    required_vars=[
        "existing_courses_xml",
        "connected_courses_xml",
        "department_xml",
        "professor_xml",
        "partial_course_xml",
        "freeform_prompt_text",
    ],
)


def get_course_prompt(
    existing_courses: List[Dict[str, Any]],
    department_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    partial_course_attrs: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
    connected_courses: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Génère une invite de cours à partir des données fournies.

    Args:
        existing_courses: Liste des dictionnaires d'attributs de cours existants.
        department_data: Dictionnaire des attributs du département.
        professor_data: Dictionnaire des attributs du professeur.
        partial_course_attrs: Dictionnaire des attributs connus ou partiels du cours.
        freeform_prompt: Texte libre optionnel pour le contexte.
        connected_courses: Cours explicitement liés pour le contexte de séquence.

    Returns:
        Chaîne d'invite formatée.
    """
    existing_courses_xml_str = courses_to_xml(existing_courses)
    connected_courses_xml_str = connected_courses_to_xml(connected_courses or [])
    department_xml_str = department_to_xml(department_data, missing_marker="[non précisé]")
    professor_xml_str = professor_to_xml(professor_data, missing_marker="[non précisé]")
    partial_course_xml_str = partial_course_to_xml(partial_course_attrs)

    freeform_prompt_text = (
        f"Contexte ou idées supplémentaires pour le cours :\n{freeform_prompt}\n"
        if freeform_prompt
        else ""
    )

    try:
        return COURSE_PROMPT.format(
            existing_courses_xml=existing_courses_xml_str,
            connected_courses_xml=connected_courses_xml_str,
            department_xml=department_xml_str,
            professor_xml=professor_xml_str,
            partial_course_xml=partial_course_xml_str,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Erreur lors du formatage de COURSE_PROMPT : {e}")
