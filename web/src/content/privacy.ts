/**
 * Privacy Policy content.
 *
 * This is the English (default) copy. If a locale-specific version is needed
 * in the future, create `privacy_es.ts`, `privacy_fr.ts`, etc. with the same
 * shape, then import the right one in `pages/AboutPrivacy.tsx` based on the
 * current locale (e.g. via `useLocale()` from `../i18n`).
 */

export type PrivacySubsection = {
  subheading: string
  paragraphs: string[]
  items?: string[]
}

export type PrivacySection = {
  heading: string
  paragraphs?: string[]
  items?: string[]
  subsections?: PrivacySubsection[]
}

export type PrivacyContent = {
  title: string
  lastUpdated: string
  intro: string
  sections: PrivacySection[]
  closing?: string
}

export const privacy: PrivacyContent = {
  title: 'Privacy Policy',
  lastUpdated: 'March 28, 2026',
  intro:
    'We collect very little data about you. We don\u2019t sell it, we don\u2019t track you across the web, we don\u2019t show you ads. Most of this site works without an account. If you do create one, we store your email and username so you can log back in.\n\nThat\u2019s it. That\u2019s the privacy policy.',
  sections: [
    {
      heading: 'What We Collect (and Why)',
      subsections: [
        {
          subheading: 'If You Browse Without Logging In',
          paragraphs: [
            'Almost nothing. You can view courses, listen to lectures, and download audio files without an account.',
            'We use Plausible Analytics \u2014 a privacy-focused analytics service that collects:',
          ],
          items: [
            'Page views (which pages get visited)',
            'General geographic region (country/city level, not precise location)',
            'Browser and device type',
            'Referral sources (how you found us)',
          ],
        },
        {
          subheading: 'If You Create an Account',
          paragraphs: [
            'Authentication: We use Auth0 for secure authentication. When you sign up, we require your email address (for login and account recovery) and a username (which you can set or change at any time). Auth0 may set cookies in your browser to keep you logged in. We don\u2019t control these cookies \u2014 they\u2019re part of Auth0\u2019s authentication system.',
            'Profile data: We store your email and username on our servers so you can create courses, lectures, and professors. That\u2019s all we keep.',
            'Preferences: Some display preferences (theme choice, volume settings, etc.) may be saved in your browser\u2019s local storage. This data never leaves your device.',
          ],
        },
        {
          subheading: 'What We Don\u2019t Collect',
          paragraphs: [],
          items: [
            'No browsing history: We don\u2019t track what you view, listen to, or download',
            'No behavioral tracking: We don\u2019t build profiles of your interests or habits',
            'No third-party tracking: No Facebook Pixel, no Google Analytics, no ad networks',
            'No precise location: We don\u2019t collect GPS data or precise geolocation',
            'No personal data beyond email/username: We don\u2019t ask for your real name, address, phone number, or anything else',
          ],
        },
      ],
    },
    {
      heading: 'How We Use Your Data',
      items: [
        'Email: To let you log in and (if necessary) reset your password. We won\u2019t email you marketing unless you explicitly opt in.',
        'Username: To attribute content you create (courses, lectures, professors) to your account.',
        'Analytics: To understand traffic patterns and improve the site.',
      ],
      paragraphs: ['That\u2019s the complete list.'],
    },
    {
      heading: 'Who We Share Data With',
      paragraphs: ['Almost nobody.'],
      items: [
        'Auth0: They handle authentication, so they see your email when you log in.',
        'Plausible Analytics: They see anonymous page views \u2014 no personal data.',
        'No one else: We don\u2019t sell data. We don\u2019t share it with advertisers, data brokers, or anyone else.',
      ],
      subsections: [
        {
          subheading: 'Legal Requests',
          paragraphs: [
            'We\u2019ll comply with valid legal requests (court orders, subpoenas) if required by law. We\u2019ll notify you unless prohibited from doing so.',
          ],
        },
      ],
    },
    {
      heading: 'Where Your Data Lives',
      paragraphs: [
        'Our servers are hosted on Amazon Web Services (AWS) in the United States. If you\u2019re in the EU, UK, or another region with strong data protection laws, this means your data crosses international borders.',
        'We don\u2019t currently participate in Privacy Shield or similar frameworks because we collect so little data it\u2019s not relevant. But if you\u2019re concerned about this, you\u2019re welcome to use the site without creating an account.',
      ],
    },
    {
      heading: 'Your Rights',
      paragraphs: ['You have the right to:'],
      items: [
        'Access your data: Email us and we\u2019ll tell you what we have (spoiler: email and username).',
        'Correct your data: You can change your username in account settings. Email us if you need to update your email.',
        'Delete your data: Email us requesting account deletion and we\u2019ll permanently remove your account, email, and username within 30 days. Note: any content you\u2019ve published (courses, lectures) will remain under Creative Commons license, but we\u2019ll disassociate it from your account.',
        'Export your data: We\u2019ll provide a JSON file of your account data if you request it.',
      ],
    },
    {
      heading: 'Data Retention',
      items: [
        'Active accounts: We keep your email and username as long as your account exists.',
        'Deleted accounts: Permanently removed within 30 days of your deletion request.',
        'Analytics: Plausible retains anonymous data for 30 days, then aggregates it.',
      ],
    },
    {
      heading: 'Security',
      paragraphs: ['We use industry-standard security practices:'],
      items: [
        'Encrypted connections (HTTPS)',
        'Secure authentication via Auth0',
        'Regular security updates',
        'No storage of passwords (Auth0 handles that)',
      ],
      subsections: [
        {
          subheading: '',
          paragraphs: [
            'But let\u2019s be honest: no system is perfectly secure. We do our best, but we can\u2019t guarantee absolute security.',
          ],
        },
      ],
    },
    {
      heading: 'Children\u2019s Privacy',
      paragraphs: [
        'ArtificialU is not directed at children under 13. We don\u2019t knowingly collect data from children. If you believe a child has created an account, email us and we\u2019ll delete it.',
      ],
    },
    {
      heading: 'Changes to This Policy',
      paragraphs: [
        'We may update this policy occasionally. We\u2019ll note the revision date at the top. Material changes will be announced on the site.',
      ],
    },
    {
      heading: 'No Ads, No Tracking, No BS',
      paragraphs: [
        'This is a passion project, not a surveillance platform. We\u2019re not here to monetize your attention or sell your data. We just want to explore what AI can do with educational content.',
        'If you have questions or concerns about privacy, email us at: ben@aliencyb.org',
      ],
    },
  ],
  closing:
    'Use the site without an account if you want maximum privacy. Create an account if you want to make stuff. Either way, we\u2019re not tracking you.',
}
