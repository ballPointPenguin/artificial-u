"""Modèles d'invites pour les cours magistraux (version française)."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    lectures_to_xml,
    partial_course_to_xml,
    professor_to_xml,
    topic_to_xml,
    topics_brief_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

LECTURE_XML_STRUCTURE = """
<lecture>
  <title>
    [Titre de la séance]
  </title>
  <content>
    [Contenu complet de la séance]
  </content>
</lecture>
"""

LECTURE_PROMPT = PromptTemplate(
    template=f"""
{{course_xml}}

{{professor_xml}}

{{topic_xml}}

{{existing_lectures_xml}}

{{topics_xml}}

{{freeform_prompt_text}}

Instructions :

1. Prenez connaissance des informations fournies pour comprendre le contexte de la séance.

2. Générez une séance d'environ {{word_count}} mots, conçue pour une narration audio immersive
   mêlant l'atmosphère d'un cours magistral, d'un podcast et d'un livre audio.

3. Structurez votre réponse dans le format XML suivant :

{LECTURE_XML_STRUCTURE}

4. Dans la section <content>, incluez les éléments suivants :
   - Titre ou thème (repris depuis la section <title>)
   - Introduction et mise en contexte
   - Points principaux et explications
   - Interactions avec les étudiants et questions (facultatif), dans un ton joueur et conversationnel
   - Exemples, analogies et anecdotes vivantes
   - Indications scéniques entre [crochets] apportant des détails sensoriels ou physiques
     concrets et non ambigus (ex. : [Clique sur la diapositive suivante : La Joconde.],
     [Trace une formule au tableau noir.]) plutôt que des signaux abstraits de ton ou de structure.
   - N'incluez PAS d'indications vocales (ex. : « voix adoptant un ton narratif »,
     « voix devenant plus intense », « voix baissant jusqu'au murmure ») car le système
     de synthèse vocale ne peut pas les interpréter et les lira littéralement.
   - Transitions naturelles entre les sujets
   - Conclusion et aperçu de la prochaine séance

5. Écrivez dans un style conversationnel, marqué par la personnalité du professeur, qui reflète
   ses particularités, son humour et sa perspective tels que décrits dans les informations
   le concernant. Privilégiez un edu-tainment imaginatif plutôt qu'une approche académique formelle.

6. Évitez les formules mathématiques complexes — exprimez-les en langage parlé adapté
   à une diffusion audio.

7. Créez un fil narratif plutôt que de simplement présenter des faits.

8. Incluez des interactions naturelles et un engagement avec le public, mais évitez les
   aspects logistiques académiques formels tels que les heures de permanence, les politiques
   de notation ou les rappels administratifs.

9. Assurez-vous que le texte convient à un moteur de synthèse vocale :
   - Un simple saut de ligne ne crée pas une pause audible ; terminez la phrase précédente
     par un point (ou une autre ponctuation fermante) avant de commencer une nouvelle ligne
     si vous souhaitez une pause notable.
   - N'utilisez PAS les MAJUSCULES pour l'emphase ; le synthétiseur les lit maladroitement.
     Exprimez l'emphase par le choix des mots, le rythme ou des propositions courtes.
   - Épellez les symboles mathématiques en toutes lettres (ex. : « égale », « plus »,
     « moins », « fois », « divisé par ») plutôt qu'avec les symboles « = », « + »,
     « - », « × », « ÷ ».
   - Évitez la ponctuation superflue telle que les astérisques ou les tirets répétés.
   - N'utilisez PAS de mise en forme markdown. Cela signifie :
     * Pas de double astérisques (**texte**) pour le gras
     * Pas d'astérisques simples (*texte*) pour l'emphase
     * Pas de dièses (#, ##, ###) pour les titres
     * Aucune emphase basée sur des astérisques
   - Tout le texte de la réponse sera lu à voix haute ; les astérisques sonneraient mal.
   - Épellez les années et les siècles en toutes lettres (ex. : « le vingtième siècle »,
     « dix-neuf soixante-neuf », « les années vingt ») plutôt que sous forme numérique
     (« XXe siècle », « 1969 », « les années 20 »).
   - Épellez les chiffres romains sous leur forme orale (ex. : « Louis le Quatorzième »
     au lieu de « Louis XIV », « la Première Guerre mondiale » au lieu de « Guerre
     mondiale I », « François le Premier » au lieu de « François Ier »).
   - Pour les sigles prononcés lettre par lettre, utilisez des points entre les lettres
     (ex. : « O.N.U. », « C.N.R.S. »), mais gardez les acronymes prononcés comme des
     mots intacts (ex. : « UNESCO », « SNCF », « radar »).
   - Pour les abréviations courantes, épellez la forme parlée (ex. : « Monsieur » au lieu
     de « M. », « contre » au lieu de « vs », « et » au lieu de « & »).

Avant de rédiger la séance finale, esquissez sa structure et ses points principaux dans
des balises <lecture_outline></lecture_outline>. Cela vous aidera à garantir une présentation
bien organisée et cohérente. Dans cette esquisse :

- Listez les thèmes principaux et les sous-thèmes de la séance.
- Donnez une brève description de la relation de chaque thème avec le cours et les séances précédentes.
- Proposez des exemples, analogies ou interactions étudiantes potentiels pour chaque thème principal.

Cette section peut être assez longue, car elle vous aidera à créer une séance complète et engageante.

Après avoir complété l'esquisse, fournissez le contenu réel de la séance dans le format XML
exact indiqué ci-dessus. Assurez-vous de fermer correctement toutes les balises XML.
La section <lecture> doit être un XML bien formé.

N'oubliez pas d'imprégner le texte de la personnalité du professeur tout en maintenant
la structure et le contenu requis.
""",
    required_vars=[
        "course_xml",
        "professor_xml",
        "topic_xml",
        "existing_lectures_xml",
        "topics_xml",
        "freeform_prompt_text",
        "word_count",
    ],
)


def get_lecture_prompt(
    course_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    topic_data: Dict[str, Any],
    existing_lectures: List[Dict[str, Any]],
    topics_data: List[Dict[str, Any]],
    freeform_prompt: Optional[str] = None,
    word_count: int = 3000,
) -> str:
    """Génère une invite de cours magistral à partir des données fournies.

    Args:
        course_data: Dictionnaire des attributs du cours.
        professor_data: Dictionnaire des attributs du professeur.
        topic_data: Dictionnaire des attributs du sujet.
        existing_lectures: Liste des dictionnaires de séances existantes.
        topics_data: Liste des dictionnaires de sujets.
        freeform_prompt: Texte libre optionnel pour le contexte.
        word_count: Nombre de mots cible pour la séance.

    Returns:
        Chaîne d'invite formatée.
    """
    course_xml_str = partial_course_to_xml(course_data)
    professor_xml_str = professor_to_xml(professor_data)
    topic_xml_str = topic_to_xml(topic_data)
    existing_lectures_xml_str = lectures_to_xml(existing_lectures)
    topics_xml_str = topics_brief_to_xml(topics_data)

    freeform_prompt_text = (
        f"Contexte ou idées supplémentaires pour la séance :\n{freeform_prompt}\n"
        if freeform_prompt
        else ""
    )

    try:
        return LECTURE_PROMPT.format(
            course_xml=course_xml_str,
            professor_xml=professor_xml_str,
            topic_xml=topic_xml_str,
            existing_lectures_xml=existing_lectures_xml_str,
            topics_xml=topics_xml_str,
            word_count=word_count,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Erreur lors du formatage de LECTURE_PROMPT : {e}")
