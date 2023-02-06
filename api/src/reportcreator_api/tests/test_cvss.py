import pytest

from reportcreator_api.pentests import cvss


@pytest.mark.parametrize("vector,score", [
    (None, 0.0),
    ('n/a', 0.0),

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

