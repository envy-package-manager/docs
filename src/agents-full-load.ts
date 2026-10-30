import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';
import siteConfig from '@generated/docusaurus.config';

// In-site links to /agents would otherwise render the themed page from the JS
// bundle. Stop the click before React Router sees it, so the browser follows the
// href normally and fetches the plain HTML that agentsPlainHtml writes.
if (ExecutionEnvironment.canUseDOM) {
  window.addEventListener(
    'click',
    (e) => {
      const a = (e.target as Element).closest?.('a[href]');
      if (!(a instanceof HTMLAnchorElement) || a.origin !== location.origin) {
        return;
      }
      if (a.pathname.replace(/\/$/, '') === `${siteConfig.baseUrl}agents`) {
        e.stopPropagation();
      }
    },
    true,
  );
}
