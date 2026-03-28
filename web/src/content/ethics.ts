/**
 * AI Usage & Ethics content.
 *
 * This is the English (default) copy. If a locale-specific version is needed
 * in the future, create `ethics_es.ts`, `ethics_fr.ts`, etc. with the same
 * shape, then import the right one in `pages/AboutAiEthics.tsx` based on the
 * current locale (e.g. via `useLocale()` from `../i18n`).
 */

export type EthicsSection = {
  heading: string
  paragraphs: string[]
  items?: string[]
}

export type EthicsContent = {
  title: string
  sections: EthicsSection[]
}

export const ethics: EthicsContent = {
  title: 'AI Usage & Ethics',
  sections: [
    {
      heading: 'What You\u2019re Listening To',
      paragraphs: [
        'ArtificialU is, at its core, an experiment in generative AI as an educational medium. The lectures you encounter here are not written by human professors, nor by some omniscient oracle. They are produced by large language models (LLMs) \u2014 commercial, cloud-hosted AI systems trained on enormous corpora of human-generated text \u2014 and you should engage with them accordingly.',
        'Every piece of lecture content carries a label indicating which model produced it and when (e.g., \u201CMade with Claude Sonnet 4.5\u201D, \u201CGenerated March 2026\u201D). Who prompted the generation, and the approximate parameters used, are also retained server-side. We think that kind of provenance matters.',
      ],
    },
    {
      heading: 'The Models We Use',
      paragraphs: [
        'Text content is generated primarily using models from Anthropic, a company whose stated mission is the responsible development and maintenance of advanced AI for the long-term benefit of humanity. Anthropic publishes substantial documentation on their safety research, evaluation methodology, and model behavior \u2014 we encourage the curious to read it. While we don\u2019t have any special relationship with Anthropic, we\u2019ve favored their models partly for technical reasons and partly because their public commitments to responsible AI development align reasonably well with the spirit of this project.',
        'Other LLM providers \u2014 Google Gemini, OpenAI, and locally-hosted models via Ollama \u2014 are also supported and may be used. The specific model is always disclosed alongside the content.',
        'We do not fine-tune, train, or otherwise modify the models we use. We write prompts; the model generates text. The distinction matters: we have no access to the model\u2019s weights, no visibility into its training data, and no ability to audit what it knows or doesn\u2019t know.',
      ],
    },
    {
      heading: 'How the Lectures Are Made',
      paragraphs: [
        'Each lecture begins with a base prompt describing the fictional professor \u2014 their name, academic background, personality, cultural context, and teaching style \u2014 extended with the specific course, topic, and any additional context for that session. We don\u2019t fence the model in tightly. The intention is to let it cook: to invite creative expression rather than constrain the output into a rote recitation.',
        'Framing the output as a lecture transcript, delivered by a fictional character, is a deliberate choice. When a model writes as someone rather than responding as itself, it tends to produce richer, more textured prose \u2014 drawing on the rhetorical habits, digressions, and stylistic tics of human academic speech. A history professor who grew up in Lagos will narrate the Scramble for Africa differently than one who grew up in Brussels. That texture is the point. We\u2019re not asking the model for capital-T Truth; we\u2019re asking it to emulate how an educated, perspectival human might explain something. The results feel more like a lecture and less like a Wikipedia article \u2014 which is, on balance, what we want.',
        'The practical implication: be critical. These lectures can contain errors, anachronisms, omissions, and the occasional confident wrongness that is the occupational hazard of both human professors and language models. The model is not Deep Thought. It is a very sophisticated pattern-matcher working from a snapshot of human knowledge. Treat its output accordingly \u2014 as a starting point for curiosity, not an endpoint for inquiry.',
      ],
    },
    {
      heading: 'The Professors',
      paragraphs: [
        'Every professor on this platform is a fictional character, created for the purpose of this project. Names, biographies, and personal anecdotes are invented. Any resemblance to real academics, living or dead, is unintentional. If you believe a professor profile or lecture content is misrepresenting or plagiarizing the work of a real person, please contact us.',
        'Professor profile images are generated using image models with prompts explicitly designed to produce stylized digital illustrations \u2014 deliberately non-photorealistic, a bit cartoonish \u2014 rather than anything that might be mistaken for a real person\u2019s likeness.',
        'Sometimes a professor will tell a personal anecdote from their fictional life. A character presented as a Nigerian economic historian might describe growing up in Lagos during the oil boom; one presented as a Qu\xe9becois sociologist might recall the 1995 referendum. We think this kind of texture can enrich a lecture, particularly when the subject matter intersects with the professor\u2019s supposed cultural experience. We also recognize that this can be handled clumsily \u2014 that putting words in the mouth of a fictional character from a particular culture, especially when the topic involves violence, colonialism, or oppression, carries real representational stakes. We don\u2019t have a perfect policy here and we\u2019re honest about that. We welcome feedback when something feels wrong.',
      ],
    },
    {
      heading: 'What We\u2019re Not Trying To Do',
      paragraphs: ['A few things this platform is not:'],
      items: [
        'A source of authoritative academic citation. AI-generated lectures should not be cited in academic work.',
        'A replacement for human educators. This is a supplement, a curiosity engine, a late-night rabbit hole \u2014 not a curriculum.',
        'A vehicle for misrepresentation. We make no claims that any lecture reflects the views of any real institution, academic, or public figure.',
      ],
    },
    {
      heading: 'Contact',
      paragraphs: [
        'If you have concerns about specific content \u2014 factual errors, suspected plagiarism, objectionable representations, or anything else \u2014 please reach out at ben@aliencyb.org.',
      ],
    },
  ],
}
