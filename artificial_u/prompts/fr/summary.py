"""Modèle d'invite pour le résumé de cours magistral (version française)."""

from artificial_u.prompts.base import PromptTemplate

SUMMARY_XML_STRUCTURE = """
<output>
  <summary>[GÉNÉRER]</summary>
</output>
"""

EXAMPLE_SUMMARY = """
<summary>
  La séance introduit la géologie glaciaire à travers des travaux pratiques, des spécimens
  et des projets cartographiques, en mettant l'accent sur l'érosion, le transport et la
  sédimentation. Elle couvre les formations régionales du Bassin parisien et du Massif
  central, notamment les moraines, les eskers et les dépôts fluvioglaciaires. Les annonces
  portent sur les protocoles de sécurité, le prochain thème consacré à la dynamique des
  glaciers et les lectures assignées.
</summary>
"""

SUMMARY_PROMPT = PromptTemplate(
    template=f"""
Générez un résumé de cours magistral en respectant cette structure XML :
{SUMMARY_XML_STRUCTURE}

Instructions :
- Tous les champs (avec [GÉNÉRER]) doivent être renseignés avec des valeurs générées.
- Résumez la transcription de cours ci-dessous en 50 à 100 mots, en couvrant les thèmes
  généraux abordés et les principales annonces ou activités.
- Produisez uniquement le résumé, encadré dans une unique balise <summary>.

Exemple :
{EXAMPLE_SUMMARY}

Transcription du cours :
{{lecture_content}}
""",
    required_vars=["lecture_content"],
)


def get_summary_prompt(lecture_content: str) -> str:
    """Génère l'invite de résumé pour un cours magistral."""
    return SUMMARY_PROMPT.format(lecture_content=lecture_content)
