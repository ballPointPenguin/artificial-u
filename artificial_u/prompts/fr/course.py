"""Modèles d'invites pour les cours (version française)."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    connected_courses_to_xml,
    courses_to_xml,
    department_to_xml,
    partial_course_to_xml,
    professor_to_xml,
    topics_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

COURSE_XML_STRUCTURE = """<course>
  <code>[Code du cours]</code>
  <title>[Intitulé du cours]</title>
  <description>[Description du cours]</description>
  <level>[Niveau du cours : "Licence" ou "Master"]</level>
  <lectures_per_week>[Nombre de séances par semaine]</lectures_per_week>
  <total_weeks>[Nombre total de semaines]</total_weeks>
  <notes>[Consigne pédagogique ou linguistique optionnelle ; omettre ou laisser vide]</notes>
  <topics>
    <topic>
      <title>[Thème hebdomadaire ou titre du sujet]</title>
      <week>[Numéro de la semaine]</week>
      <order>[Ordre dans la semaine]</order>
      <content>
        <lecture>[Titre ou description évocatrice de la séance]</lecture>
        <readings>
          <reading>[Ouvrage de référence, article ou texte primaire]</reading>
          <reading>[Lecture 2]</reading>
        </readings>
        <objectives>
          <objective>[Objectif d'apprentissage 1]</objective>
          <objective>[Objectif d'apprentissage 2]</objective>
        </objectives>
      </content>
    </topic>
  </topics>
</course>"""

EXAMPLE_COURSE_1 = """<course>
  <code>PHIL215</code>
  <title>Philosophie de l'esprit et de la conscience</title>
  <description>Une enquête sur la nature de la vie mentale, l'expérience subjective, l'identité
  personnelle et l'intelligence artificielle, du dualisme cartésien aux sciences cognitives
  contemporaines.</description>
  <level>Licence</level>
  <lectures_per_week>1</lectures_per_week>
  <total_weeks>4</total_weeks>
  <topics>
    <topic>
      <title>Le « problème difficile » de la conscience</title>
      <week>1</week>
      <order>1</order>
      <content>
        <lecture>Qu'est-ce que cela fait d'être une chauve-souris ? Définir l'expérience subjective</lecture>
        <readings>
          <reading>Nagel, Thomas. « What Is It Like to Be a Bat ? »</reading>
          <reading>Chalmers, David. « Faire face au problème de la conscience ».</reading>
        </readings>
        <objectives>
          <objective>Distinguer la conscience phénoménale de l'explication fonctionnelle</objective>
        </objectives>
      </content>
    </topic>
    <topic>
      <title>Physicalisme et qualia</title>
      <week>2</week>
      <order>1</order>
      <content>
        <lecture>La chambre de Mary et l'argument de la connaissance</lecture>
        <readings>
          <reading>Jackson, Frank. « Epiphenomenal Qualia ».</reading>
          <reading>Dennett, Daniel. La Conscience expliquée (extraits).</reading>
        </readings>
        <objectives>
          <objective>Évaluer les réponses physicalistes à l'argument de la connaissance</objective>
        </objectives>
      </content>
    </topic>
  </topics>
</course>"""

COURSE_PROMPT = PromptTemplate(
    template=f"""
Générez un cours universitaire complet ainsi que son programme hebdomadaire (syllabus) au format XML,
en transformant des sujets généraux, des idées libres ou des références à des chercheurs, auteurs et
penseurs en un cursus cohérent et rigoureux.

Structure XML :
{COURSE_XML_STRUCTURE}

Étapes et consignes :
1. Définir l'identité du cours :
   - `<code>` et `<title>` : Créez un code de cours pertinent et un intitulé académique évocateur.
   - `<description>` : Rédigez une présentation concise de style catalogue synthétisant la portée
     intellectuelle et la problématique centrale du cours.
   - `<level>` : Choisissez "Licence" ou "Master" selon la complexité et le public cible.
   - `<total_weeks>` et `<lectures_per_week>` :
     - Par défaut, prévoyez 10 à 12 semaines et 1 sujet principal par semaine, ou passez à 2 sujets
       par semaine lorsque le champ est vaste ou interdisciplinaire (maximum 3 séances par semaine).
     - Respectez toute valeur explicitement demandée par l'utilisateur.
   - `<notes>` (optionnel) :
     - Omettez `<notes>` ou laissez-le vide par défaut. Ne copiez PAS l'invite brute de
       l'utilisateur et ne répétez pas la description du cours ici.
     - Ne remplissez `<notes>` avec une consigne claire et concise que si l'invite contient une
       directive pédagogique, stylistique, de format ou de langue importante pour la rédaction des
       futures séances (ex. : « Bien qu'il s'agisse d'un cours de mathématiques, privilégiez une
       approche narrative adaptée à l'audio sans formules lourdes »). Si `<user_notes>` figure déjà
       dans les détails partiels, conservez-la ou affinez-la.

2. Concevoir le programme semaine par semaine (`<topics>`) :
   - Organisez la matière selon une progression logique de modules `<topic>` couvrant chaque créneau
     de la semaine 1 à `total_weeks` et de l'ordre 1 à `lectures_per_week` (`total_weeks * lectures_per_week`
     éléments `<topic>` au total).
   - `<title>` : Attribuez à chaque créneau un thème conceptuel clair qui nourrit la réflexion globale du cours.
   - `<content>` :
     - `<lecture>` : Incluez un titre de séance incisif ou une brève description conceptuelle.
     - `<readings>` : Associez à chaque sujet des suggestions de lectures pertinentes (ouvrages fondateurs,
       articles, essais ou sources primaires).
     - `<objectives>` (facultatif) et `<notes>` (facultatif) : Objectifs d'apprentissage ou contexte.

3. Ton et garde-fous :
   - Académique et concis : Adoptez un style érudit, informatif et synthétique qui privilégie la structure
     conceptuelle et les liens intellectuels.
   - Le fond avant la logistique : Concentrez-vous strictement sur l'architecture intellectuelle (thèmes,
     séances, lectures). N'incluez pas de clauses administratives (barèmes, règles d'assiduité) ni de séances
     de « bilan / récapitulatif » sans contenu nouveau.
   - Échappez les caractères sensibles au XML dans les nœuds de texte, notamment `&` (`&amp;`),
     `<` (`&lt;`) et `>` (`&gt;`).
   - Si un brouillon de programme est déjà fourni ci-dessous accompagné de nouvelles consignes de l'utilisateur,
     considérez les détails du cours et les sujets existants comme un brouillon de travail et révisez tous les
     champs (`title`, `code`, `description`, `level`, `lectures_per_week`, `total_weeks`) ainsi que `<topics>`
     nécessaires pour répondre aux modifications demandées.

Cours existants (pour le contexte et éviter les répétitions) :
{{existing_courses_xml}}

Cours liés (prérequis ou séquences explicites — alignez-vous avec eux) :
{{connected_courses_xml}}
{{related_courses_topics_context}}
Informations sur le département :
{{department_xml}}

Informations sur le professeur :
{{professor_xml}}

Informations partielles sur le cours :
{{partial_course_xml}}
{{existing_topics_context}}
{{freeform_prompt_text}}

Exemple de cours correctement formaté (abrégé à 2 semaines pour l'exemple) :
{EXAMPLE_COURSE_1}

Encadrez votre réponse dans des balises <output>, en fournissant uniquement l'élément <course> (avec son bloc <topics>).
""",
    required_vars=[
        "existing_courses_xml",
        "connected_courses_xml",
        "related_courses_topics_context",
        "department_xml",
        "professor_xml",
        "partial_course_xml",
        "existing_topics_context",
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
    existing_topics: Optional[List[Dict[str, Any]]] = None,
    related_courses_topics_context: Optional[str] = None,
) -> str:
    """Génère une invite de cours + programme à partir des données fournies.

    Args:
        existing_courses: Liste des dictionnaires d'attributs de cours existants.
        department_data: Dictionnaire des attributs du département.
        professor_data: Dictionnaire des attributs du professeur.
        partial_course_attrs: Dictionnaire des attributs connus ou partiels du cours.
        freeform_prompt: Texte libre optionnel pour le contexte ou les consignes de révision.
        connected_courses: Cours explicitement liés pour le contexte de séquence.
        existing_topics: Liste optionnelle des sujets du brouillon actuel lors d'une révision.
        related_courses_topics_context: Contexte optionnel des sujets des cours liés.

    Returns:
        Chaîne d'invite formatée.
    """
    existing_courses_xml_str = courses_to_xml(existing_courses)
    connected_courses_xml_str = connected_courses_to_xml(connected_courses or [])
    department_xml_str = department_to_xml(department_data, missing_marker="[non précisé]")
    professor_xml_str = professor_to_xml(professor_data, missing_marker="[non précisé]")
    partial_course_xml_str = partial_course_to_xml(partial_course_attrs)

    topics_list = existing_topics or partial_course_attrs.get("topics")
    existing_topics_context = ""
    if topics_list:
        existing_topics_xml = topics_to_xml(topics_list)
        existing_topics_context = (
            "\nSujets actuels du brouillon de programme (révisez et mettez à jour ces sujets "
            f"ainsi que les détails du cours selon les consignes de l'utilisateur) :\n{existing_topics_xml}\n"
        )

    related_context = (
        f"\n{related_courses_topics_context}\n" if related_courses_topics_context else ""
    )

    freeform_prompt_text = (
        f"Consignes / idées de l'utilisateur pour le cours :\n{freeform_prompt}\n"
        if freeform_prompt
        else ""
    )

    try:
        return COURSE_PROMPT.format(
            existing_courses_xml=existing_courses_xml_str,
            connected_courses_xml=connected_courses_xml_str,
            related_courses_topics_context=related_context,
            department_xml=department_xml_str,
            professor_xml=professor_xml_str,
            partial_course_xml=partial_course_xml_str,
            existing_topics_context=existing_topics_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Erreur lors du formatage de COURSE_PROMPT : {e}")
