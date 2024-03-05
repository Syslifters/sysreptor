import pytest
from reportcreator_api.utils.concurrent_editing import ChangeSet, Update, rebase_updates


class TestTextTransformations:
    def assert_changes(self, text, changes, expected):
        change_set = ChangeSet.from_dict(changes)
        res = change_set.apply(text)
        assert res == expected
        return res

    def test_changes(self):
        operations = [
            # Write first line (without linebreak)
            {'changes': [[0, "line1"]], 'expected': 'line1'},
            # Insert newline
            {'changes': [5, [0, '', '']], 'expected': 'line1\n'},
            # Write second line
            {'changes': [6, [0, 'line2']], 'expected': 'line1\nline2'},
            # Insert multiline
            {'changes': [11, [0, '', 'line3', 'line4', '']], 'expected': 'line1\nline2\nline3\nline4\n'},
            # Prepend line
            {'changes': [[0, 'line0', ''], 24], 'expected': 'line0\nline1\nline2\nline3\nline4\n'},
            # Delete lines
            {'changes': [11, [12], 7], 'expected': 'line0\nline1\nline4\n'},
            # Replace char
            {'changes': [16, [1, '2'], 1], 'expected': 'line0\nline1\nline2\n'},
            # Replace multiple chars (at different positions)
            {'changes': [[1, 'L'], 5, [1, 'L'], 5, [1, 'L'], 5], 'expected': 'Line0\nLine1\nLine2\n'},
            # Delete multiple chars (at different positions)
            {'changes': [1, [1], 1, [1], 3, [1], 1, [1], 3, [1], 1, [1], 2], 'expected': 'Ln0\nLn1\nLn2\n'},
            # Type character for character
            {'changes': [12, [0, 'L']], 'expected': 'Ln0\nLn1\nLn2\nL'},
            {'changes': [13, [0, 'n']], 'expected': 'Ln0\nLn1\nLn2\nLn'},
            {'changes': [14, [0, '4']], 'expected': 'Ln0\nLn1\nLn2\nLn4'},
            {'changes': [14, [1]], 'expected': 'Ln0\nLn1\nLn2\nLn'},
            {'changes': [14, [0, '3']], 'expected': 'Ln0\nLn1\nLn2\nLn3'},
        ]

        # Loading and serialization
        for op in operations:
            assert ChangeSet.from_dict(op['changes']).to_dict() == op['changes']

        # Apply changes in order
        text = ''
        for op in operations:
            text = self.assert_changes(text=text, changes=op['changes'], expected=op['expected'])

        # Combine changes
        combined_change = ChangeSet.from_dict(operations[0]['changes'])
        for op in operations[1:]:
            combined_change = combined_change.compose(ChangeSet.from_dict(op['changes']))
            assert combined_change.apply('') == op['expected']

    @pytest.mark.parametrize(['text', 'change1', 'change2', 'expected'], [
        ('line1\nline2\n', [4, [1, '0'], 7], [10, [1, '1'], 1], 'line0\nline1\n'),
        ('line1\nline2\n', [5, [0, '', ''], 7], [7, [3], 2], 'line1\n\nl2\n'),
        ('line1\nline2\n', [5, [7]], [9, [0, 'e'], 3], 'line1e'),
        ('ABCDE', [1, [1], 3], [3, [1], 1], 'ACE'),
        ('AD', [1, [0, 'B'], 1], [1, [0, 'C'], 1], 'ABCD'),
    ])
    def test_operational_transform(self, text, change1, change2, expected):
        c1 = ChangeSet.from_dict(change1)
        c2 = ChangeSet.from_dict(change2)
        assert c1.compose(c2.map(c1)).apply(text) == expected
        assert c2.compose(c1.map(c2, True)).apply(text) == expected
        
        text1 = c1.apply(text)
        updates = rebase_updates(updates=[Update(client_id='c2', changes=c2)], over=[Update(client_id='c1', changes=c1)])
        assert len(updates) == 1
        assert updates[0].changes.apply(text1) == expected

        # Rebase already applied changes
        assert rebase_updates(updates=[Update(client_id='c2', changes=c2)], over=[Update(client_id='c1', changes=c1), Update(client_id='c2', changes=c2)]) == []

    