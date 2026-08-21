import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const organizationName = 'envy-package-manager';
const projectName = 'docs';

const config: Config = {
  title: 'envy',
  tagline: "what's yours... is mine.",
  favicon: 'img/favicon.png',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Production URL. GitHub Pages serves this repo at
  // https://envy-package-manager.github.io/docs/
  url: `https://${organizationName}.github.io`,
  baseUrl: `/${projectName}/`,

  // GitHub Pages deployment config.
  organizationName,
  projectName,

  // Anything that would ship a broken link fails the build, which is what makes
  // the CI workflow a link checker.
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
      onBrokenMarkdownImages: 'throw',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: `https://github.com/${organizationName}/${projectName}/tree/main/`,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
        sitemap: {
          lastmod: 'date',
          changefreq: null,
          priority: null,
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Placeholder Open Graph card. Replace with a purpose-built 1200x630 image.
    image: 'img/Ruckus.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'envy',
      logo: {
        alt: 'Ruckus, the envy mascot',
        src: 'img/Ruckus.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: `https://github.com/${organizationName}`,
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Introduction', to: '/'},
            {label: 'Getting Started', to: '/getting-started'},
            {label: 'Concepts', to: '/concepts'},
            {label: 'CLI Reference', to: '/reference/cli'},
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'GitHub',
              href: `https://github.com/${organizationName}`,
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} envy contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['lua', 'bash', 'powershell', 'json'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
