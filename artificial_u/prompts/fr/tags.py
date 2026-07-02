from typing import Any, Dict, List, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TAGS_XML_STRUCTURE = """<tags>
  <tag>[Nom du tag]</tag>
  <tag>[Autre nom de tag]</tag>
</tags>"""

EXAMPLE_TAGS = """<tags>
  <tag>Philosophie de l'Esprit</tag>
  <tag>Conscience</tag>
  <tag>Sciences Cognitives</tag>
  <tag>Neurosciences</tag>
</tags>"""

# Limite du contexte de programme pour ne pas surcharger l'invite
MAX_TOPIC_TITLES = 30

COURSE_TAGS_PROMPT = PromptTemplate(
    template=f"""
Générez des tags thématiques pour le cours universitaire décrit ci-dessous.

Règles :
- Retournez entre 3 et 7 éléments `<tag>`.
- Chaque tag est une courte expression nominale en français, d'un à trois mots,
  avec une majuscule initiale.
- Les tags décrivent le contenu du cours : domaines, thèmes et méthodes.
  Un tag sur le niveau ou le caractère du cours (p. ex. « Introduction », « Pratique »)
  est bienvenu s'il est distinctif.
- Privilégiez FORTEMENT la réutilisation des tags du vocabulaire existant lorsqu'ils
  conviennent ; n'inventez un nouveau tag que si rien dans le vocabulaire ne s'applique.
- Ne vous contentez pas de répéter le nom du département ; les tags doivent apporter
  une information supplémentaire.
- Pas de doublons ni de quasi-doublons (p. ex. ne retournez pas à la fois
  « Éthique » et « Éthiques »).
- Échappez les caractères sensibles en XML dans les nœuds de texte,
  en particulier `&`, `<` et `>`.

Structure XML requise :
{TAGS_XML_STRUCTURE}

Informations sur le cours :
{{course_xml}}
{{department_context}}{{topics_context}}{{vocabulary_context}}
Exemple de sortie correctement formatée :
{EXAMPLE_TAGS}

Encadrez votre réponse dans des balises <output>, en fournissant uniquement
l'élément <tags>.
""",
    required_vars=[
        "course_xml",
        "department_context",
        "topics_context",
        "vocabulary_context",
    ],
)


def get_course_tags_prompt(
    course_data: Dict[str, Any],
    *,
    department_name: Optional[str] = None,
    topic_titles: Optional[List[str]] = None,
    existing_tags: Optional[List[str]] = None,
) -> str:
    """Génère l'invite de création de tags pour un cours.

    Args:
        course_data: Attributs du cours (code, titre, description, niveau, ...)
        department_name: Nom du département qui offre le cours
        topic_titles: Titres des sujets du programme du cours
        existing_tags: Vocabulaire de tags existant à privilégier, du plus utilisé au moins utilisé
    """
    course_xml_str = partial_course_to_xml(course_data)

    department_context = f"Département : {department_name}\n" if department_name else ""

    topics_context = ""
    if topic_titles:
        titles = "\n".join(f"- {title}" for title in topic_titles[:MAX_TOPIC_TITLES])
        topics_context = f"Titres des sujets du programme du cours :\n{titles}\n"

    vocabulary_context = ""
    if existing_tags:
        vocabulary = "\n".join(f"- {name}" for name in existing_tags)
        vocabulary_context = (
            "Vocabulaire de tags existant (du plus utilisé au moins utilisé, "
            f"à réutiliser de préférence) :\n{vocabulary}\n"
        )

    try:
        return COURSE_TAGS_PROMPT.format(
            course_xml=course_xml_str,
            department_context=department_context,
            topics_context=topics_context,
            vocabulary_context=vocabulary_context,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting COURSE_TAGS_PROMPT: {e}")
