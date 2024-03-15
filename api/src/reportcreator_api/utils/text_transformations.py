"""
This file is based on code from @codemirror/state and @codemirror/collab.

MIT License

Copyright (C) 2018-2021 by Marijn Haverbeke <marijn@haverbeke.berlin> and others

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import dataclasses
from typing import Optional

from reportcreator_api.utils.utils import get_at


@dataclasses.dataclass
class ChangeSet:
    sections: list[int]
    inserted: list[str]

    @property
    def empty(self):
        """
        False when there are actual changes in this set.
        """
        return len(self.sections) == 0 or (len(self.sections) == 2 and self.sections[1] < 0)
    
    @property
    def length(self):
        """
        The length of the document before the change.
        """
        result = 0
        for i in range(0, len(self.sections), 2):
            result += self.sections[i]
        return result

    @classmethod
    def from_dict(cls, changes: list):
        sections = []
        inserted = []
        for i, part in enumerate(changes):
            if isinstance(part, int):
                sections.extend([part, -1])
            elif not isinstance(part, list) or len(part) == 0 or not isinstance(part[0], int) or not all(map(lambda e: isinstance(e, str), part[1:])):
                raise ValueError(f'Invalid change')
            else:
                while len(inserted) <= i:
                    inserted.append('')  # Text.empty
                inserted[i] = '\n'.join(part[1:])
                sections.extend([part[0], len(inserted[i])])
        return ChangeSet(sections=sections, inserted=inserted)
    
    def to_dict(self):
        """
        Serialize this change set to a JSON-representable value.
        """
        parts = []
        for i in range(0, len(self.sections), 2):
            i_len = self.sections[i]
            ins = self.sections[i + 1]
            if ins < 0:
                parts.append(i_len)
            elif ins == 0:
                parts.append([i_len])
            else:
                parts.append([i_len] + self.inserted[i >> 1].split('\n'))
        return parts

    def map_desc(self, other: 'ChangeSet', before: bool):
        """
        Compute the combined effect of applying another set of changes
        after this one. The length of the document after this set should
        match the length before `other`.
        """
        return map_set(self, other, before)

    def compose(self, other: 'ChangeSet'):
        """
        Compute the combined effect of applying another set of changes
        after this one. The length of the document after this set should
        match the length before `other`.
        """
        if self.empty:
            return other
        elif other.empty:
            return self
        else:
            return compose_sets(self, other)

    def map(self, other: 'ChangeSet', before=False):
        """
        Given another change set starting in the same document, maps this
        change set over the other, producing a new change set that can be
        applied to the document produced by applying `other`. When
        `before` is `true`, order changes as if `this` comes before
        `other`, otherwise (the default) treat `other` as coming first.
        
        Given two changes `A` and `B`, `A.compose(B.map(A))` and
        `B.compose(A.map(B, true))` will produce the same document. This
        provides a basic form of [operational
        transformation](https://en.wikipedia.org/wiki/Operational_transformation),
        and can be used for collaborative editing.
        """
        if other.empty:
            return self
        else:
            return map_set(self, other, before)
        
    def iter_changes(self, individual):
        pos_a = 0
        pos_b = 0
        i = 0
        while i < len(self.sections):
            i_len = self.sections[i]
            ins = self.sections[i + 1]
            i += 2
            if ins < 0:
                pos_a += i_len
                pos_b += i_len
            else:
                end_a = pos_a
                end_b = pos_b
                text = ''
                while True:
                    end_a += i_len
                    end_b += ins
                    if ins and self.inserted is not None:
                        text += self.inserted[(i - 2) >> 1]
                    if individual or i == len(self.sections) or self.sections[i + 1] < 0:
                        break
                    i_len = self.sections[i]
                    ins = self.sections[i + 1]
                    i += 2
                yield (pos_a, end_a, pos_b, end_b, text)
                pos_a = end_a
                pos_b = end_b

        
    def apply(self, doc: str):
        """
        Apply the changes in this set to a document, returning the new
        document.
        """
        # Normalize line breaks to get consistent positions
        doc = doc.replace('\r\n', '\n')

        if self.length != len(doc):
            raise ValueError(f'Applying change set to a document with the wrong length')
        for (from_a, to_a, from_b, to_b, text) in self.iter_changes(False):
            doc = doc[:from_b] + text + doc[from_b + (to_a - from_a):]
        return doc
        


@dataclasses.dataclass
class Update:
    client_id: str
    version: float
    changes: ChangeSet


class SectionIter:
    def __init__(self, set: ChangeSet):
        self.set = set
        self.i = 0
        self.len = 0
        self.off = 0
        self.ins = 0
        self.next()

    @property
    def done(self):
        return self.ins == -2
    
    @property
    def text(self):
        index = (self.i - 2) >> 1
        return '' if index >= len(self.set.inserted) else self.set.inserted[index]
    
    @property
    def len2(self):
        return self.len if self.ins < 0 else self.ins
    
    def next(self):
        if self.i < len(self.set.sections):
            self.len = self.set.sections[self.i]
            self.ins = self.set.sections[self.i + 1]
            self.i += 2
        else:
            self.len = 0
            self.ins = -2
        self.off = 0
    
    def forward(self, i_len: int):
        if i_len == self.len:
            self.next()
        else:
            self.len -= i_len
            self.off += i_len
    
    def forward2(self, i_len: int):
        if self.ins == -1:
            self.forward(i_len)
        elif i_len == self.ins:
            self.next()
        else:
            self.ins -= i_len
            self.off += i_len

    def text_bit(self, i_len: Optional[int]=None):
        index = (self.i - 2) >> 1
        if index >= len(self.set.inserted) and not i_len:
            return ''
        elif i_len is not None:
            return self.set.inserted[index][self.off:self.off + i_len]
        else:
            return self.set.inserted[index][self.off:]


def add_section(sections: list[int], i_len: int, ins: int, force_join=False):
    if i_len == 0 and ins < 0:
        return
    
    last = len(sections) - 2
    if last >= 0 and ins < 0 and ins == sections[last + 1]:
        sections[last] += i_len
    elif i_len == 0 and get_at(sections, last) == 0:
        sections[last + 1] += ins
    elif force_join:
        sections[last] += i_len
        sections[last + 1] += ins
    else:
        sections.extend([i_len, ins])


def add_insert(values: list[str], sections: list[int], value: str):
    if len(value) == 0:
        return
    
    index = (len(sections) - 2) >> 1
    if index < len(values):
        values[-1] += value
    else:
        while len(values) < index:
            values.append('')
        values.append(value)


def map_set(setA: ChangeSet, setB: ChangeSet, before: bool):
    """
    Produce a copy of setA that applies to the document after setB
    has been applied (assuming both start at the same document).
    """
    sections = []
    insert = []

    # Iterate over both sets in parallel. inserted tracks, for changes
    # in A that have to be processed piece-by-piece, whether their
    # content has been inserted already, and refers to the section index.
    a = SectionIter(setA)
    b = SectionIter(setB)
    inserted = -1
    while True:
        if a.ins == -1 and b.ins == -1:
            # Move across ranges skipped by both sets.
            i_len = min(a.len, b.len)
            add_section(sections, i_len, -1)
            a.forward(i_len)
            b.forward(i_len)
        elif b.ins >= 0 and (a.ins < 0 or inserted == a.i or a.off == 0 and (b.len < a.len or b.len == a.len and not before)):
            # If there's a change in B that comes before the next change in
            # A (ordered by start pos, then len, then before flag),
            # skip that (and process any changes in A it covers).
            i_len = b.len
            add_section(sections, b.ins, -1)
            while i_len > 0:
                piece = min(a.len, i_len)
                if a.ins >= 0 and inserted < a.i and a.len <= piece:
                    add_section(sections, 0, a.ins)
                    if insert is not None:
                        add_insert(insert, sections, a.text)
                    inserted = a.i
                a.forward(piece)
                i_len -= piece
            b.next()
        elif a.ins >= 0:
            # Process the part of a change in A up to the start of the next
            # non-deletion change in B (if overlapping).
            i_len = 0
            left = a.len
            while left > 0:
                if b.ins == -1:
                    piece = min(left, b.len)
                    i_len += piece
                    left -= piece
                    b.forward(piece)
                elif b.ins == 0 and b.len < left:
                    left -= b.len
                    b.next()
                else:
                    break
            add_section(sections, i_len, a.ins if inserted < a.i else 0)
            if insert is not None and inserted < a.i:
                add_insert(insert, sections, a.text)
            inserted = a.i
            a.forward(a.len - left)
        elif a.done and b.done:
            return ChangeSet(sections, insert)
        else:
            raise ValueError('Mismatched change set lengths')


def compose_sets(setA: ChangeSet, setB: ChangeSet):
    sections = []
    insert = []

    a = SectionIter(setA)
    b = SectionIter(setB)
    open = False
    while True:
        if a.done and b.done:
            return ChangeSet(sections, insert)
        elif a.ins == 0:
            # Deletion in A
            add_section(sections, a.len, 0, open)
            a.next()
        elif b.len == 0 and not b.done:
            # Insertion in B
            add_section(sections, 0, b.ins, open)
            if insert is not None:
                add_insert(insert, sections, b.text)
            b.next()
        elif a.done or b.done:
            raise ValueError('Mismatched change set lengths')
        else:
            i_len = min(a.len2, b.len)
            section_len = len(sections)
            if a.ins == -1:
                ins_b = -1 if b.ins == -1 else \
                        0 if b.off else \
                        b.ins
                add_section(sections, i_len, ins_b, open)
                if insert is not None and ins_b:
                    add_insert(insert, sections, b.text)
            elif b.ins == -1:
                add_section(sections, 0 if a.off else a.len, i_len, open)
                if insert is not None:
                    add_insert(insert, sections, a.text_bit(i_len))
            else:
                add_section(sections, 0 if a.off else a.len, 0 if b.off else b.ins, open)
                if insert is not None and not b.off:
                    add_insert(insert, sections, b.text)
            
            open = (a.ins > i_len or (b.ins >= 0 and b.len > i_len)) and (open or len(sections) > section_len)
            a.forward2(i_len)
            b.forward(i_len)


def rebase_updates(updates: list[Update], over: list[Update]) -> list[Update]:
    """
    Rebase and deduplicate an array of client-submitted updates that
    came in with an out-of-date version number. `over` should hold the
    updates that were accepted since the given version (or at least
    their change descs and client IDs). Will return an array of
    updates that, firstly, has updates that were already accepted
    filtered out, and secondly, has been moved over the other changes
    so that they apply to the current document version.
    """
    import logging
    logging.info(f'rebase_updates: updates={updates}, over={over}')

    if not updates or not over:
        return updates
    
    changes = None
    skip = 0
    version = None
    for update in over:
        other = updates[skip] if skip < len(updates) else None
        if other and other.client_id == update.client_id:
            if changes:
                changes = changes.map_desc(other.changes, True)
            skip += 1
        else:
            if changes:
                changes = changes.compose(update.changes)
            else:
                changes = update.changes
        if version is None or update.version > version:
            version = update.version
    
    if skip:
        updates = updates[skip:]
    
    if not changes:
        return updates
    else:
        out = []
        for update in updates:
            updated_changes = update.changes.map(changes)
            changes = changes.map_desc(update.changes, True)
            out.append(Update(
                client_id=update.client_id,
                version=version,
                changes=updated_changes
            ))
        return out
