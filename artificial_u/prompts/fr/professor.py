"""Modèles d'invites pour les profils de professeurs (version française)."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import partial_professor_to_xml, professors_to_xml
from artificial_u.prompts.base import PromptTemplate

PROFESSOR_XML_STRUCTURE = (
    "<professor>\n"
    "  <name>[GÉNÉRER]</name>\n"
    "  <title>[GÉNÉRER]</title>\n"
    "  <department_name>[GÉNÉRER]</department_name>\n"
    "  <specialization>[GÉNÉRER]</specialization>\n"
    "  <gender>[GÉNÉRER]</gender>\n"
    "  <age>[GÉNÉRER]</age>\n"
    "  <accent>[GÉNÉRER]</accent>\n"
    "  <description>[GÉNÉRER]</description>\n"
    "  <background>[GÉNÉRER]</background>\n"
    "  <personality>[GÉNÉRER]</personality>\n"
    "  <teaching_style>[GÉNÉRER]</teaching_style>\n"
    "</professor>"
)

EXAMPLE_PROFESSOR_1 = (
    "<professor>\n"
    "  <name>Professeure Isabelle Moreau</name>\n"
    "  <title>Maîtresse de conférences</title>\n"
    "  <department_name>Littérature Comparée</department_name>\n"
    "  <specialization>Littérature française du vingtième siècle</specialization>\n"
    "  <gender>Féminin</gender>\n"
    "  <age>52</age>\n"
    "  <accent>Parisien cultivé</accent>\n"
    "  <description>Tenue sobre et élégante, souvent en tons sombres. Regard vif, "
    "expression précise. Cheveux courts et grisonnants.</description>\n"
    "  <background>Doctorat à l'École Normale Supérieure. Auteure de deux monographies "
    "sur Sartre et de Beauvoir.</background>\n"
    "  <personality>Intellectuellement rigoureuse, elle pousse ses étudiants à remettre "
    "en question leurs certitudes et apprécie les arguments nuancés.</personality>\n"
    "  <teaching_style>Séminaires de discussion approfondis, lecture attentive des textes "
    "et exigences élevées en matière de participation.</teaching_style>\n"
    "</professor>"
)

PARTIAL_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}
Complétez le profil de professeur ci-dessous.
Utilisez les informations déjà fournies. Pour les champs marqués [GÉNÉRER], inventez
des valeurs réalistes et cohérentes.

Professeurs déjà présents dans l'université (pour le contexte et éviter les répétitions) :
{{existing_professors_xml}}

Informations partielles fournies (utilisez-les si disponibles, générez pour [GÉNÉRER]) :
{{partial_profile_xml}}

Format de sortie souhaité (remplissez tous les espaces réservés) :
{PROFESSOR_XML_STRUCTURE}

Exemple de profil complet :
{EXAMPLE_PROFESSOR_1}

Générez le profil complet.
Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <professor>.
""",
    required_vars=[
        "existing_professors_xml",
        "partial_profile_xml",
    ],
)

OPEN_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}
Générez un profil de professeur détaillé d'après le contexte et l'inspiration ci-dessus.
Créez un profil académique complet et réaliste incluant le département, la spécialisation
et tous les détails personnels. Consultez la liste des professeurs existants pour assurer
la variété et éviter les répétitions.

Professeurs existants dans le même département :
{{existing_professors_xml}}

Format de sortie souhaité (remplissez tous les espaces réservés) :
{PROFESSOR_XML_STRUCTURE}

Exemple de profil complet :
{EXAMPLE_PROFESSOR_1}

Générez le profil complet du professeur.
Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <professor>.
""",
    required_vars=["existing_professors_xml"],
)

GUIDED_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}

En vous inspirant de la description ci-dessus comme guide, créez un profil de professeur
qui en capture l'essence, le style et les caractéristiques. Vous devez créer un professeur
qui incarne les qualités, le parcours et l'approche pédagogique décrits.
Consultez la liste des professeurs existants pour assurer la variété et éviter les répétitions.

Professeurs existants dans le même département :
{{existing_professors_xml}}

Format de sortie souhaité (remplissez tous les espaces réservés) :
{PROFESSOR_XML_STRUCTURE}

Exemple de profil complet :
{EXAMPLE_PROFESSOR_1}

Générez le profil du professeur correspondant à la description fournie.
Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <professor>.
""",
    required_vars=["existing_professors_xml"],
)


def get_professor_prompt(
    existing_professors: Optional[List[Dict[str, str]]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Sélectionne et formate l'invite de génération de professeur adaptée.

    Args:
        existing_professors: Liste des professeurs existants (dicts nom/spécialisation)
            pour le contexte.
        partial_attributes: Dictionnaire optionnel d'attributs connus.
        freeform_prompt: Texte libre optionnel pour des orientations supplémentaires.

    Returns:
        La chaîne d'invite formatée prête pour le LLM.
    """
    existing_professors = existing_professors or []
    existing_professors_xml_str = professors_to_xml(existing_professors)
    partial_attributes = partial_attributes or {}

    if freeform_prompt:
        if not partial_attributes:
            prompt_text = f"INSPIRATION ET CONTEXTE :\n{freeform_prompt}\n\n"
            return GUIDED_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                freeform_prompt_text=prompt_text,
            )
        else:
            prompt_text = (
                f"CONTEXTE ET ORIENTATION :\n{freeform_prompt}\n\n"
                "Utilisez ce contexte pour guider la complétion du profil ci-dessous.\n\n"
            )
            partial_profile_xml_str = partial_professor_to_xml(partial_attributes)
            return PARTIAL_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                partial_profile_xml=partial_profile_xml_str,
                freeform_prompt_text=prompt_text,
            )
    else:
        if not partial_attributes:
            prompt_text = (
                "Créez un profil de professeur réaliste et détaillé avec des "
                "caractéristiques inventées.\n\n"
            )
            return OPEN_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                freeform_prompt_text=prompt_text,
            )
        else:
            prompt_text = ""
            partial_profile_xml_str = partial_professor_to_xml(partial_attributes)
            return PARTIAL_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                partial_profile_xml=partial_profile_xml_str,
                freeform_prompt_text=prompt_text,
            )
