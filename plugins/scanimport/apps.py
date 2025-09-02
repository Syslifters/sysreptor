from sysreptor.plugins import PluginConfig


class ScanImportPluginConfig(PluginConfig):
    """
    Import scan results from various tools.
    Supported tools: Burp, Nessus, Nmap, OpenVAS, Qualys, SSLyze, ZAP
    """

    plugin_id = '2335e86b-198c-4e6c-9563-8190a05ee38c'
    professional_only = True

