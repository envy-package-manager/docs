import {readFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {themes as prismThemes} from 'prism-react-renderer';
import type {Config, Plugin} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const organizationName = 'envy-package-manager';
const projectName = 'docs';

// Overwrite the built /agents page with the raw markdown in a bare <pre>: no
// JS, no CSS, no navbar. ~33 KB instead of ~90 KB. The client module turns
// in-site navigation to /agents into a full page load so humans get it too.
function agentsPlainHtml({siteDir}: {siteDir: string}): Plugin {
  return {
    name: 'agents-plain-html',
    getClientModules() {
      return [join(siteDir, 'src/agents-full-load.ts')];
    },
    async postBuild({outDir}) {
      const md = readFileSync(join(siteDir, 'docs/agents.md'), 'utf8')
        .replace(/^---\n[\s\S]*?\n---\n+/, '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;');
      writeFileSync(
        join(outDir, 'agents/index.html'),
        `<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n` +
          `<title>envy for agents</title>\n<pre style="white-space:pre-wrap">\n${md}</pre>\n`,
      );
    },
  };
}

const config: Config = {
  title: 'envy',
  tagline: "what's yours... is mine.",
  favicon: 'img/favicon.png',

  future: {
    v4: true,
  },

  url: `https://${organizationName}.github.io`,
  baseUrl: `/${projectName}/`,

  organizationName,
  projectName,

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

  plugins: [agentsPlainHtml],

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
          href: `https://github.com/${organizationName}/envy/releases/latest`,
          label: 'Latest Release',
          position: 'right',
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
      copyright: `envy is public domain: <a href="https://github.com/${organizationName}/envy/blob/main/LICENSE">0BSD or the Unlicense</a>, your choice. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: [
        'lua',
        'bash',
        'powershell',
        'json',
        'makefile',
        'batch',
        'cmake',
        'diff',
        'ignore',
        'shell-session',
      ],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
