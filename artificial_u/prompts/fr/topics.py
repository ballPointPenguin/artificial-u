"""Modèles d'invites pour les sujets de cours (version française)."""

from typing import Any, Dict, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TOPIC_XML_STRUCTURE = """<topic>
  <title>[Titre du sujet]</title>
  <week>[Numéro de la semaine]</week>
  <order>[Ordre dans la semaine]</order>
  <content>
    <lecture>[Titre ou description de la séance]</lecture>
    <readings>
      <reading>[Lecture 1]</reading>
      <reading>[Lecture 2]</reading>
    </readings>
    <objectives>
      <objective>[Objectif d'apprentissage 1]</objective>
      <objective>[Objectif d'apprentissage 2]</objective>
    </objectives>
    <notes>[Notes ou contexte supplémentaires]</notes>
  </content>
</topic>"""

EXAMPLE_TOPIC = """<topic>
  <title>Le « problème difficile » de la conscience</title>
  <week>1</week>
  <order>1</order>
  <content>
    <lecture>Qu'est-ce que cela fait d'être une chauve-souris ? Définir l'expérience subjective</lecture>
    <readings>
      <reading>Chalmers, David. « Faire face au problème de la conscience ».</reading>
      <reading>Nagel, Thomas. « What Is It Like to Be a Bat ? »</reading>
    </readings>
    <objectives>
      <objective>Définir le problème difficile de la conscience</objective>
      <objective>Distinguer l'expérience subjective de l'explication fonctionnelle</objective>
    </objectives>
  </content>
</topic>"""

NEXT_TOPIC_PROMPT = PromptTemplate(
    template=f"""
Générez exactement un sujet de cours au format XML.

Vous remplissez un créneau canonique dans la séquence du cours.
Le cours comporte {{lectures_per_week}} sujets par semaine sur {{total_weeks}} semaines,
pour un total de {{total_topic_slots}} créneaux thématiques.
Générez le sujet pour :
- Semaine {{target_week}}
- Sujet {{target_order}} dans cette semaine
- Créneau canonique {{target_slot_index}} sur {{total_topic_slots}}

Règles importantes :
- Retournez exactement un élément `<topic>` pour le créneau demandé.
- La valeur de `<week>` doit être `{{target_week}}`.
- La valeur de `<order>` doit être `{{target_order}}`.
- Utilisez le contexte des sujets précédents pour maintenir la progression et éviter les doublons.
- Ce sujet doit introduire un contenu substantiel pour son créneau.
- Échappez les caractères sensibles au XML dans les nœuds de texte, notamment `&`, `<` et `>`.
- Ne produisez pas de récapitulatif, de conclusion ou de « bilan de cours » à moins que la
  description du cours ne l'implique explicitement, et même dans ce cas, le sujet doit
  introduire de nouvelles notions.

Pour le sujet, vous pouvez inclure du contenu flexible avec ces structures simples :
- Éléments uniques : <lecture>texte</lecture>, <notes>texte</notes>
- Listes : <readings><reading>texte</reading><reading>texte</reading></readings>
- Éléments courants : lecture, readings, objectives, concepts, notes

Tous les éléments de contenu sont facultatifs. Gardez le contenu simple et académique.

Structure XML requise :
{TOPIC_XML_STRUCTURE}

Informations sur le cours :
{{course_xml}}

{{prior_topics_context}}
{{related_courses_topics_context}}

{{freeform_prompt_text}}

Exemple de sujet correctement formaté :
{EXAMPLE_TOPIC}

Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <topic>.
""",
    required_vars=[
        "course_xml",
        "lectures_per_week",
        "total_weeks",
        "total_topic_slots",
        "target_week",
        "target_order",
        "target_slot_index",
        "prior_topics_context",
        "related_courses_topics_context",
        "freeform_prompt_text",
    ],
)


def get_next_topic_prompt(
    course_data: Dict[str, Any],
    *,
    target_week: int,
    target_order: int,
    prior_topics_xml: Optional[str] = None,
    related_courses_topics_context: Optional[str] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Génère l'invite pour un créneau thématique canonique du cours."""
    course_xml_str = partial_course_to_xml(course_data)
    lectures_per_week = int(course_data.get("lectures_per_week") or 1)
    total_weeks = int(course_data.get("total_weeks") or 1)
    total_topic_slots = lectures_per_week * total_weeks
    target_slot_index = ((target_week - 1) * lectures_per_week) + target_order

    freeform_prompt_text = (
        f"Contexte ou idées supplémentaires pour les sujets :\n{freeform_prompt}\n"
        if freeform_prompt
        else ""
    )

    prior_topics_context = ""
    if prior_topics_xml:
        prior_topics_context = (
            f"Sujets déjà établis dans le cours :\n{prior_topics_xml}\n\n"
            "Construisez naturellement à partir d'eux. Évitez les doublons, les récapitulatifs "
            "inutiles et les formulations prématurées de fin de cours.\n"
        )
    related_courses_context = related_courses_topics_context or ""

    try:
        return NEXT_TOPIC_PROMPT.format(
            course_xml=course_xml_str,
            lectures_per_week=lectures_per_week,
            total_weeks=total_weeks,
            total_topic_slots=total_topic_slots,
            target_week=target_week,
            target_order=target_order,
            target_slot_index=target_slot_index,
            prior_topics_context=prior_topics_context,
            related_courses_topics_context=related_courses_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Erreur lors du formatage de NEXT_TOPIC_PROMPT : {e}")
