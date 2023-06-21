import { DefaultExternalServices } from "pdfjs-dist/lib/web/app";
import { DownloadManager } from "pdfjs-dist/lib/web/download_manager";
import { GenericScripting } from "pdfjs-dist/lib/web/generic_scripting";
import { BasePreferences } from "pdfjs-dist/lib/web/preferences";
import { NullL10n } from 'pdfjs-dist/lib/web/l10n_utils';


class FakePreferences extends BasePreferences {
  async _writeToStorage(prefObj) {}
  async _readFromStorage(prefObj) {}
}


export default class GenericExternalServices extends DefaultExternalServices {
  static createDownloadManager() {
    return new DownloadManager();
  }

  static createPreferences() {
    return new FakePreferences();
  }

  static createL10n() {
    return Object.assign({}, NullL10n, {
      async get(key, args = null) {
        if (key === 'of_pages') {
          return await NullL10n.get(key, args, "/ {{ pagesCount }}");
        } else if (key === 'find_match_count') {
          return await NullL10n.get(key, args, "{{ current }} of {{ total }}");
        } else if (key === 'find_not_found') {
          return await NullL10n.get(key, args, "No results");
        } else if (['find_reached_top', 'find_reached_bottom'].includes(key)) {
          return null;
        } else {
          return await NullL10n.get(key, args);
        }
      }
    })
  }

  static createScripting({ sandboxBundleSrc }) {
    return new GenericScripting(sandboxBundleSrc);
  }
}
