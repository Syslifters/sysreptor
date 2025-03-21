import pytest

from sysreptor.pentests import cvss


@pytest.mark.parametrize(("vector", "score"), [
    (None, 0.0),
    ('n/a', 0.0),

    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H', 10.0),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N', 0.0),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N', 9.3),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:H/SI:H/SA:H', 7.9),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H/E:U', 9.1),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H/MVI:L/MSA:S', 9.8),
    ('CVSS:4.0/AV:P/AC:H/AT:P/PR:H/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N', 1.0),
    ('CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:P/VC:N/VI:H/VA:H/SC:N/SI:L/SA:L', 5.2),
    ('CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:P/VC:N/VI:H/VA:H/SC:N/SI:L/SA:L/E:P/CR:H/IR:M/AR:H/MAV:A/MAT:P/MPR:N/MVI:H/MVA:N/MSI:H/MSA:N/S:N/V:C/U:Amber', 4.7),
    ('CVSS:4.0/AV:N/AC:H/AT:N/PR:H/UI:N/VC:N/VI:N/VA:H/SC:H/SI:H/SA:H/CR:L/IR:L/AR:L', 5.8),
    ('CVSS:4.0/AV:F/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N', 0.0),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/ui:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N', 0.0),
    ('CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/SC:N/SI:N/SA:N', 0.0),

    ('CVSS:3.0/AV:N', 0.0),
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/XX:X', 0.0),
    ('CVSS:3.0/AV:J/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L', 0.0),
    ('CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N', 0.0),
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L', 4.6),
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L', 5.5),
    ('CVSS:3.0/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L', 7.0),
    ('CVSS:3.0/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H', 9.9),
    ('CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H', 10.0),
    ('CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:T/RC:U', 8.4),
    ('CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:X/RC:U/CR:M/IR:H/AR:X/MAV:A/MAC:L/MPR:L/MUI:R/MS:U/MC:L/MI:L/MA:X', 5.7),

    ('CVSS:3.1/AV:N', 0.0),
    ('CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/XX:X', 0.0),
    ('CVSS:3.1/AV:J/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L', 0.0),
    ('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N', 0.0),
    ('CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L', 4.6),
    ('CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L', 5.5),
    ('CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L', 7.0),
    ('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H', 10.0),
    ('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N/CR:H', 10.0),
    ('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H', 9.9),
    ('CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:H', 9.0),
    ('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:T/RC:U', 8.4),
    ('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:X/RC:U/CR:M/IR:H/AR:X/MAV:A/MAC:L/MPR:L/MUI:R/MS:U/MC:L/MI:L/MA:X', 5.7),

    ('CVSS2#AV:N', 0.0),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:N/XX:X', 0.0),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:J', 0.0),
    ('AV:N/AC:L/Au:N/C:N/I:N/A:N', 0.0),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:N', 6.4),
    ('AV:N/AC:M/Au:M/C:P/I:C/A:N', 6.4),
    ('AV:N/AC:L/Au:N/C:C/I:C/A:C', 10.0),
    ('CVSS2#AV:N/AC:L/Au:N/C:P/I:N/A:N', 5.0),
    ('AV:N/AC:M/Au:M/C:P/I:C/A:N/E:F/RL:TF/RC:C', 5.5),
    ('AV:N/AC:M/Au:M/C:P/I:C/A:N/E:F/RL:TF/RC:C/CDP:MH/TD:L/CR:H/IR:M/AR:L', 1.9),
    ('AV:N/AC:M/Au:M/C:P/I:C/A:N/E:F/RL:ND/RC:C/CDP:ND/TD:H/CR:H/IR:M/AR:ND', 6.4),
])
def test_cvss(vector, score):
    assert cvss.calculate_score(vector) == score


@pytest.mark.parametrize(("vector", "metrics"), [
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L', {
        "version": "3.0",
        "base": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "temporal": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "environmental": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "final": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
    }),
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/E:P', {
        "version": "3.0",
        "base": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "temporal": {
            "score": 4.4,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "environmental": {
            "score": 4.4,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "final": {
            "score": 4.4,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
    }),
    ('CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/E:P/MAC:L/MC:H', {
        "version": "3.0",
        "base": {
            "score": 4.6,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "temporal": {
            "score": 4.4,
            "exploitability": 1.181753232,
            "impact": 3.3733761599999994,
        },
        "environmental": {
            "score": 6.4,
            "exploitability": 2.0680681560000003,
            "impact": 4.70139168,
        },
        "final": {
            "score": 6.4,
            "exploitability": 2.0680681560000003,
            "impact": 4.70139168,
        },
    }),
    ('CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L', {
        "version": "3.1",
        "base": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "temporal": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "environmental": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.2614179224506845,
        },
        "final": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
    }),
    ('CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L/RL:O', {
        "version": "3.1",
        "base": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "temporal": {
            "score": 6.7,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "environmental": {
            "score": 6.7,
            "exploitability": 1.181753232,
            "impact": 5.2614179224506845,
        },
        "final": {
            "score": 6.7,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
    }),
    ('CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L/RL:O/CR:H/MPR:H', {
        "version": "3.1",
        "base": {
            "score": 7.0,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "temporal": {
            "score": 6.7,
            "exploitability": 1.181753232,
            "impact": 5.268807630773988,
        },
        "environmental": {
            "score": 7.1,
            "exploitability": 0.69514896,
            "impact": 6.123536263797863,
        },
        "final": {
            "score": 7.1,
            "exploitability": 0.69514896,
            "impact": 6.123536263797863,
        },
    }),
    ('CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H', {
        "version": "3.1",
        "base": {
            "score": 9.9,
            "exploitability": 3.1096342200000002,
            "impact": 6.0477304915445185,
        },
        "temporal": {
            "score": 9.9,
            "exploitability": 3.1096342200000002,
            "impact": 6.0477304915445185,
        },
        "environmental": {
            "score": 10.0,
            "exploitability": 3.1096342200000002,
            "impact": 6.1280263288099786,
        },
        "final": {
            "score": 9.9,
            "exploitability": 3.1096342200000002,
            "impact": 6.0477304915445185,
        },
    }),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:N', {
        "version": "2",
        "base": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "temporal": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "environmental": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "final": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
    }),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:N/E:U', {
        "version": "2",
        "base": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "temporal": {
            "score": 5.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "environmental": {
            "score": 5.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "final": {
            "score": 5.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
    }),
    ('CVSS2#AV:N/AC:M/Au:M/C:P/I:C/A:N/E:U/CDP:L/CR:H', {
        "version": "2",
        "base": {
            "score": 6.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "temporal": {
            "score": 5.4,
            "exploitability": 5.49,
            "impact": 7.843935000000001,
        },
        "environmental": {
            "score": 6.1,
            "exploitability": 5.49,
            "impact": 8.34033585,
        },
        "final": {
            "score": 6.1,
            "exploitability": 5.49,
            "impact": 8.34033585,
        },
    }),
])
def test_cvss_metrics(vector, metrics):
    assert cvss.calculate_metrics(vector) == metrics
