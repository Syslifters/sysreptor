#!/usr/bin/env bash

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Any subsequent(*) commands which fail will cause the shell script to exit immediately

allow_only="MIT"
allow_only="$allow_only;MIT License"
allow_only="$allow_only;CMU License (MIT-CMU)"
allow_only="$allow_only;BSD"
allow_only="$allow_only;BSD License"
allow_only="$allow_only;Apache Software License"
allow_only="$allow_only;Apache-2.0"
allow_only="$allow_only;GNU Library or Lesser General Public License (LGPL)"
allow_only="$allow_only;GNU Lesser General Public License v2 or later (LGPLv2+)"
allow_only="$allow_only;GNU Lesser General Public License v3 (LGPLv3)"
allow_only="$allow_only;Mozilla Public License 1.0 (MPL)"
allow_only="$allow_only;Mozilla Public License 1.1 (MPL 1.1)"
allow_only="$allow_only;Mozilla Public License 2.0 (MPL 2.0)"
allow_only="$allow_only;Historical Permission Notice and Disclaimer (HPND)"
allow_only="$allow_only;Python Software Foundation License"
allow_only="$allow_only;Zope Public License"
allow_only="$allow_only;ISC License (ISCL)"
allow_only="$allow_only;The Unlicense (Unlicense)"

ignore="webencodings"
ignore="$ignore pyphen"
ignore="$ignore freetype2"
ignore="$ignore cwe"
ignore="$ignore randomcolor"
ignore="$ignore attrs"
ignore="$ignore referencing"
ignore="$ignore typing_extensions"
ignore="$ignore pytest-asyncio"
ignore="$ignore pillow"
ignore="$ignore urllib3"
ignore="$ignore pikepdf"

pip-licenses --allow-only "$allow_only" --ignore-packages $ignore >/dev/null
pip-licenses -l --no-license-path -f plain-vertical --no-version --ignore-packages $ignore > NOTICE

# Those packages do not include valid license files
webencodings=$(cat << EOF
BSD License
Copyright (c) 2012 by Simon Sapin.

Some rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

    * The names of the contributors may not be used to endorse or
      promote products derived from this software without specific
      prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
EOF
)

pyphen=$(cat << EOF
Mozilla Public License 1.1 (MPL 1.1)
                          MOZILLA PUBLIC LICENSE
                                Version 1.1

                              ---------------

1. Definitions.

     1.0.1. "Commercial Use" means distribution or otherwise making the
     Covered Code available to a third party.

     1.1. "Contributor" means each entity that creates or contributes to
     the creation of Modifications.

     1.2. "Contributor Version" means the combination of the Original
     Code, prior Modifications used by a Contributor, and the Modifications
     made by that particular Contributor.

     1.3. "Covered Code" means the Original Code or Modifications or the
     combination of the Original Code and Modifications, in each case
     including portions thereof.

     1.4. "Electronic Distribution Mechanism" means a mechanism generally
     accepted in the software development community for the electronic
     transfer of data.

     1.5. "Executable" means Covered Code in any form other than Source
     Code.

     1.6. "Initial Developer" means the individual or entity identified
     as the Initial Developer in the Source Code notice required by Exhibit
     A.

     1.7. "Larger Work" means a work which combines Covered Code or
     portions thereof with code not governed by the terms of this License.

     1.8. "License" means this document.

     1.8.1. "Licensable" means having the right to grant, to the maximum
     extent possible, whether at the time of the initial grant or
     subsequently acquired, any and all of the rights conveyed herein.

     1.9. "Modifications" means any addition to or deletion from the
     substance or structure of either the Original Code or any previous
     Modifications. When Covered Code is released as a series of files, a
     Modification is:
          A. Any addition to or deletion from the contents of a file
          containing Original Code or previous Modifications.

          B. Any new file that contains any part of the Original Code or
          previous Modifications.

     1.10. "Original Code" means Source Code of computer software code
     which is described in the Source Code notice required by Exhibit A as
     Original Code, and which, at the time of its release under this
     License is not already Covered Code governed by this License.

     1.10.1. "Patent Claims" means any patent claim(s), now owned or
     hereafter acquired, including without limitation,  method, process,
     and apparatus claims, in any patent Licensable by grantor.

     1.11. "Source Code" means the preferred form of the Covered Code for
     making modifications to it, including all modules it contains, plus
     any associated interface definition files, scripts used to control
     compilation and installation of an Executable, or source code
     differential comparisons against either the Original Code or another
     well known, available Covered Code of the Contributor's choice. The
     Source Code can be in a compressed or archival form, provided the
     appropriate decompression or de-archiving software is widely available
     for no charge.

     1.12. "You" (or "Your")  means an individual or a legal entity
     exercising rights under, and complying with all of the terms of, this
     License or a future version of this License issued under Section 6.1.
     For legal entities, "You" includes any entity which controls, is
     controlled by, or is under common control with You. For purposes of
     this definition, "control" means (a) the power, direct or indirect,
     to cause the direction or management of such entity, whether by
     contract or otherwise, or (b) ownership of more than fifty percent
     (50%) of the outstanding shares or beneficial ownership of such
     entity.

2. Source Code License.

     2.1. The Initial Developer Grant.
     The Initial Developer hereby grants You a world-wide, royalty-free,
     non-exclusive license, subject to third party intellectual property
     claims:
          (a)  under intellectual property rights (other than patent or
          trademark) Licensable by Initial Developer to use, reproduce,
          modify, display, perform, sublicense and distribute the Original
          Code (or portions thereof) with or without Modifications, and/or
          as part of a Larger Work; and

          (b) under Patents Claims infringed by the making, using or
          selling of Original Code, to make, have made, use, practice,
          sell, and offer for sale, and/or otherwise dispose of the
          Original Code (or portions thereof).

          (c) the licenses granted in this Section 2.1(a) and (b) are
          effective on the date Initial Developer first distributes
          Original Code under the terms of this License.

          (d) Notwithstanding Section 2.1(b) above, no patent license is
          granted: 1) for code that You delete from the Original Code; 2)
          separate from the Original Code;  or 3) for infringements caused
          by: i) the modification of the Original Code or ii) the
          combination of the Original Code with other software or devices.

     2.2. Contributor Grant.
     Subject to third party intellectual property claims, each Contributor
     hereby grants You a world-wide, royalty-free, non-exclusive license

          (a)  under intellectual property rights (other than patent or
          trademark) Licensable by Contributor, to use, reproduce, modify,
          display, perform, sublicense and distribute the Modifications
          created by such Contributor (or portions thereof) either on an
          unmodified basis, with other Modifications, as Covered Code
          and/or as part of a Larger Work; and

          (b) under Patent Claims infringed by the making, using, or
          selling of  Modifications made by that Contributor either alone
          and/or in combination with its Contributor Version (or portions
          of such combination), to make, use, sell, offer for sale, have
          made, and/or otherwise dispose of: 1) Modifications made by that
          Contributor (or portions thereof); and 2) the combination of
          Modifications made by that Contributor with its Contributor
          Version (or portions of such combination).

          (c) the licenses granted in Sections 2.2(a) and 2.2(b) are
          effective on the date Contributor first makes Commercial Use of
          the Covered Code.

          (d)    Notwithstanding Section 2.2(b) above, no patent license is
          granted: 1) for any code that Contributor has deleted from the
          Contributor Version; 2)  separate from the Contributor Version;
          3)  for infringements caused by: i) third party modifications of
          Contributor Version or ii)  the combination of Modifications made
          by that Contributor with other software  (except as part of the
          Contributor Version) or other devices; or 4) under Patent Claims
          infringed by Covered Code in the absence of Modifications made by
          that Contributor.

3. Distribution Obligations.

     3.1. Application of License.
     The Modifications which You create or to which You contribute are
     governed by the terms of this License, including without limitation
     Section 2.2. The Source Code version of Covered Code may be
     distributed only under the terms of this License or a future version
     of this License released under Section 6.1, and You must include a
     copy of this License with every copy of the Source Code You
     distribute. You may not offer or impose any terms on any Source Code
     version that alters or restricts the applicable version of this
     License or the recipients' rights hereunder. However, You may include
     an additional document offering the additional rights described in
     Section 3.5.

     3.2. Availability of Source Code.
     Any Modification which You create or to which You contribute must be
     made available in Source Code form under the terms of this License
     either on the same media as an Executable version or via an accepted
     Electronic Distribution Mechanism to anyone to whom you made an
     Executable version available; and if made available via Electronic
     Distribution Mechanism, must remain available for at least twelve (12)
     months after the date it initially became available, or at least six
     (6) months after a subsequent version of that particular Modification
     has been made available to such recipients. You are responsible for
     ensuring that the Source Code version remains available even if the
     Electronic Distribution Mechanism is maintained by a third party.

     3.3. Description of Modifications.
     You must cause all Covered Code to which You contribute to contain a
     file documenting the changes You made to create that Covered Code and
     the date of any change. You must include a prominent statement that
     the Modification is derived, directly or indirectly, from Original
     Code provided by the Initial Developer and including the name of the
     Initial Developer in (a) the Source Code, and (b) in any notice in an
     Executable version or related documentation in which You describe the
     origin or ownership of the Covered Code.

     3.4. Intellectual Property Matters
          (a) Third Party Claims.
          If Contributor has knowledge that a license under a third party's
          intellectual property rights is required to exercise the rights
          granted by such Contributor under Sections 2.1 or 2.2,
          Contributor must include a text file with the Source Code
          distribution titled "LEGAL" which describes the claim and the
          party making the claim in sufficient detail that a recipient will
          know whom to contact. If Contributor obtains such knowledge after
          the Modification is made available as described in Section 3.2,
          Contributor shall promptly modify the LEGAL file in all copies
          Contributor makes available thereafter and shall take other steps
          (such as notifying appropriate mailing lists or newsgroups)
          reasonably calculated to inform those who received the Covered
          Code that new knowledge has been obtained.

          (b) Contributor APIs.
          If Contributor's Modifications include an application programming
          interface and Contributor has knowledge of patent licenses which
          are reasonably necessary to implement that API, Contributor must
          also include this information in the LEGAL file.

               (c)    Representations.
          Contributor represents that, except as disclosed pursuant to
          Section 3.4(a) above, Contributor believes that Contributor's
          Modifications are Contributor's original creation(s) and/or
          Contributor has sufficient rights to grant the rights conveyed by
          this License.

     3.5. Required Notices.
     You must duplicate the notice in Exhibit A in each file of the Source
     Code.  If it is not possible to put such notice in a particular Source
     Code file due to its structure, then You must include such notice in a
     location (such as a relevant directory) where a user would be likely
     to look for such a notice.  If You created one or more Modification(s)
     You may add your name as a Contributor to the notice described in
     Exhibit A.  You must also duplicate this License in any documentation
     for the Source Code where You describe recipients' rights or ownership
     rights relating to Covered Code.  You may choose to offer, and to
     charge a fee for, warranty, support, indemnity or liability
     obligations to one or more recipients of Covered Code. However, You
     may do so only on Your own behalf, and not on behalf of the Initial
     Developer or any Contributor. You must make it absolutely clear than
     any such warranty, support, indemnity or liability obligation is
     offered by You alone, and You hereby agree to indemnify the Initial
     Developer and every Contributor for any liability incurred by the
     Initial Developer or such Contributor as a result of warranty,
     support, indemnity or liability terms You offer.

     3.6. Distribution of Executable Versions.
     You may distribute Covered Code in Executable form only if the
     requirements of Section 3.1-3.5 have been met for that Covered Code,
     and if You include a notice stating that the Source Code version of
     the Covered Code is available under the terms of this License,
     including a description of how and where You have fulfilled the
     obligations of Section 3.2. The notice must be conspicuously included
     in any notice in an Executable version, related documentation or
     collateral in which You describe recipients' rights relating to the
     Covered Code. You may distribute the Executable version of Covered
     Code or ownership rights under a license of Your choice, which may
     contain terms different from this License, provided that You are in
     compliance with the terms of this License and that the license for the
     Executable version does not attempt to limit or alter the recipient's
     rights in the Source Code version from the rights set forth in this
     License. If You distribute the Executable version under a different
     license You must make it absolutely clear that any terms which differ
     from this License are offered by You alone, not by the Initial
     Developer or any Contributor. You hereby agree to indemnify the
     Initial Developer and every Contributor for any liability incurred by
     the Initial Developer or such Contributor as a result of any such
     terms You offer.

     3.7. Larger Works.
     You may create a Larger Work by combining Covered Code with other code
     not governed by the terms of this License and distribute the Larger
     Work as a single product. In such a case, You must make sure the
     requirements of this License are fulfilled for the Covered Code.

4. Inability to Comply Due to Statute or Regulation.

     If it is impossible for You to comply with any of the terms of this
     License with respect to some or all of the Covered Code due to
     statute, judicial order, or regulation then You must: (a) comply with
     the terms of this License to the maximum extent possible; and (b)
     describe the limitations and the code they affect. Such description
     must be included in the LEGAL file described in Section 3.4 and must
     be included with all distributions of the Source Code. Except to the
     extent prohibited by statute or regulation, such description must be
     sufficiently detailed for a recipient of ordinary skill to be able to
     understand it.

5. Application of this License.

     This License applies to code to which the Initial Developer has
     attached the notice in Exhibit A and to related Covered Code.

6. Versions of the License.

     6.1. New Versions.
     Netscape Communications Corporation ("Netscape") may publish revised
     and/or new versions of the License from time to time. Each version
     will be given a distinguishing version number.

     6.2. Effect of New Versions.
     Once Covered Code has been published under a particular version of the
     License, You may always continue to use it under the terms of that
     version. You may also choose to use such Covered Code under the terms
     of any subsequent version of the License published by Netscape. No one
     other than Netscape has the right to modify the terms applicable to
     Covered Code created under this License.

     6.3. Derivative Works.
     If You create or use a modified version of this License (which you may
     only do in order to apply it to code which is not already Covered Code
     governed by this License), You must (a) rename Your license so that
     the phrases "Mozilla", "MOZILLAPL", "MOZPL", "Netscape",
     "MPL", "NPL" or any confusingly similar phrase do not appear in your
     license (except to note that your license differs from this License)
     and (b) otherwise make it clear that Your version of the license
     contains terms which differ from the Mozilla Public License and
     Netscape Public License. (Filling in the name of the Initial
     Developer, Original Code or Contributor in the notice described in
     Exhibit A shall not of themselves be deemed to be modifications of
     this License.)

7. DISCLAIMER OF WARRANTY.

     COVERED CODE IS PROVIDED UNDER THIS LICENSE ON AN "AS IS" BASIS,
     WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING,
     WITHOUT LIMITATION, WARRANTIES THAT THE COVERED CODE IS FREE OF
     DEFECTS, MERCHANTABLE, FIT FOR A PARTICULAR PURPOSE OR NON-INFRINGING.
     THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE COVERED CODE
     IS WITH YOU. SHOULD ANY COVERED CODE PROVE DEFECTIVE IN ANY RESPECT,
     YOU (NOT THE INITIAL DEVELOPER OR ANY OTHER CONTRIBUTOR) ASSUME THE
     COST OF ANY NECESSARY SERVICING, REPAIR OR CORRECTION. THIS DISCLAIMER
     OF WARRANTY CONSTITUTES AN ESSENTIAL PART OF THIS LICENSE. NO USE OF
     ANY COVERED CODE IS AUTHORIZED HEREUNDER EXCEPT UNDER THIS DISCLAIMER.

8. TERMINATION.

     8.1.  This License and the rights granted hereunder will terminate
     automatically if You fail to comply with terms herein and fail to cure
     such breach within 30 days of becoming aware of the breach. All
     sublicenses to the Covered Code which are properly granted shall
     survive any termination of this License. Provisions which, by their
     nature, must remain in effect beyond the termination of this License
     shall survive.

     8.2.  If You initiate litigation by asserting a patent infringement
     claim (excluding declatory judgment actions) against Initial Developer
     or a Contributor (the Initial Developer or Contributor against whom
     You file such action is referred to as "Participant")  alleging that:

     (a)  such Participant's Contributor Version directly or indirectly
     infringes any patent, then any and all rights granted by such
     Participant to You under Sections 2.1 and/or 2.2 of this License
     shall, upon 60 days notice from Participant terminate prospectively,
     unless if within 60 days after receipt of notice You either: (i)
     agree in writing to pay Participant a mutually agreeable reasonable
     royalty for Your past and future use of Modifications made by such
     Participant, or (ii) withdraw Your litigation claim with respect to
     the Contributor Version against such Participant.  If within 60 days
     of notice, a reasonable royalty and payment arrangement are not
     mutually agreed upon in writing by the parties or the litigation claim
     is not withdrawn, the rights granted by Participant to You under
     Sections 2.1 and/or 2.2 automatically terminate at the expiration of
     the 60 day notice period specified above.

     (b)  any software, hardware, or device, other than such Participant's
     Contributor Version, directly or indirectly infringes any patent, then
     any rights granted to You by such Participant under Sections 2.1(b)
     and 2.2(b) are revoked effective as of the date You first made, used,
     sold, distributed, or had made, Modifications made by that
     Participant.

     8.3.  If You assert a patent infringement claim against Participant
     alleging that such Participant's Contributor Version directly or
     indirectly infringes any patent where such claim is resolved (such as
     by license or settlement) prior to the initiation of patent
     infringement litigation, then the reasonable value of the licenses
     granted by such Participant under Sections 2.1 or 2.2 shall be taken
     into account in determining the amount or value of any payment or
     license.

     8.4.  In the event of termination under Sections 8.1 or 8.2 above,
     all end user license agreements (excluding distributors and resellers)
     which have been validly granted by You or any distributor hereunder
     prior to termination shall survive termination.

9. LIMITATION OF LIABILITY.

     UNDER NO CIRCUMSTANCES AND UNDER NO LEGAL THEORY, WHETHER TORT
     (INCLUDING NEGLIGENCE), CONTRACT, OR OTHERWISE, SHALL YOU, THE INITIAL
     DEVELOPER, ANY OTHER CONTRIBUTOR, OR ANY DISTRIBUTOR OF COVERED CODE,
     OR ANY SUPPLIER OF ANY OF SUCH PARTIES, BE LIABLE TO ANY PERSON FOR
     ANY INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES OF ANY
     CHARACTER INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF GOODWILL,
     WORK STOPPAGE, COMPUTER FAILURE OR MALFUNCTION, OR ANY AND ALL OTHER
     COMMERCIAL DAMAGES OR LOSSES, EVEN IF SUCH PARTY SHALL HAVE BEEN
     INFORMED OF THE POSSIBILITY OF SUCH DAMAGES. THIS LIMITATION OF
     LIABILITY SHALL NOT APPLY TO LIABILITY FOR DEATH OR PERSONAL INJURY
     RESULTING FROM SUCH PARTY'S NEGLIGENCE TO THE EXTENT APPLICABLE LAW
     PROHIBITS SUCH LIMITATION. SOME JURISDICTIONS DO NOT ALLOW THE
     EXCLUSION OR LIMITATION OF INCIDENTAL OR CONSEQUENTIAL DAMAGES, SO
     THIS EXCLUSION AND LIMITATION MAY NOT APPLY TO YOU.

10. U.S. GOVERNMENT END USERS.

     The Covered Code is a "commercial item," as that term is defined in
     48 C.F.R. 2.101 (Oct. 1995), consisting of "commercial computer
     software" and "commercial computer software documentation," as such
     terms are used in 48 C.F.R. 12.212 (Sept. 1995). Consistent with 48
     C.F.R. 12.212 and 48 C.F.R. 227.7202-1 through 227.7202-4 (June 1995),
     all U.S. Government End Users acquire Covered Code with only those
     rights set forth herein.

11. MISCELLANEOUS.

     This License represents the complete agreement concerning subject
     matter hereof. If any provision of this License is held to be
     unenforceable, such provision shall be reformed only to the extent
     necessary to make it enforceable. This License shall be governed by
     California law provisions (except to the extent applicable law, if
     any, provides otherwise), excluding its conflict-of-law provisions.
     With respect to disputes in which at least one party is a citizen of,
     or an entity chartered or registered to do business in the United
     States of America, any litigation relating to this License shall be
     subject to the jurisdiction of the Federal Courts of the Northern
     District of California, with venue lying in Santa Clara County,
     California, with the losing party responsible for costs, including
     without limitation, court costs and reasonable attorneys' fees and
     expenses. The application of the United Nations Convention on
     Contracts for the International Sale of Goods is expressly excluded.
     Any law or regulation which provides that the language of a contract
     shall be construed against the drafter shall not apply to this
     License.

12. RESPONSIBILITY FOR CLAIMS.

     As between Initial Developer and the Contributors, each party is
     responsible for claims and damages arising, directly or indirectly,
     out of its utilization of rights under this License and You agree to
     work with Initial Developer and Contributors to distribute such
     responsibility on an equitable basis. Nothing herein is intended or
     shall be deemed to constitute any admission of liability.

13. MULTIPLE-LICENSED CODE.

     Initial Developer may designate portions of the Covered Code as
     "Multiple-Licensed".  "Multiple-Licensed" means that the Initial
     Developer permits you to utilize portions of the Covered Code under
     Your choice of the NPL or the alternative licenses, if any, specified
     by the Initial Developer in the file described in Exhibit A.

EXHIBIT A -Mozilla Public License.

     ``The contents of this file are subject to the Mozilla Public License
     Version 1.1 (the "License"); you may not use this file except in
     compliance with the License. You may obtain a copy of the License at
     http://www.mozilla.org/MPL/

     Software distributed under the License is distributed on an "AS IS"
     basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
     License for the specific language governing rights and limitations
     under the License.

     The Original Code is ______________________________________.

     The Initial Developer of the Original Code is ________________________.
     Portions created by ______________________ are Copyright (C) ______
     _______________________. All Rights Reserved.

     Contributor(s): ______________________________________.

     Alternatively, the contents of this file may be used under the terms
     of the _____ license (the  "[___] License"), in which case the
     provisions of [______] License are applicable instead of those
     above.  If you wish to allow use of your version of this file only
     under the terms of the [____] License and not to allow others to use
     your version of this file under the MPL, indicate your decision by
     deleting  the provisions above and replace  them with the notice and
     other provisions required by the [___] License.  If you do not delete
     the provisions above, a recipient may use your version of this file
     under either the MPL or the [___] License."

     [NOTE: The text of this Exhibit A may differ slightly from the text of
     the notices in the Source Code files of the Original Code. You should
     use the text of this Exhibit A rather than the text found in the
     Original Code Source Code for Your Modifications.]
EOF
)

freetype2=$(cat << EOF
                    The FreeType Project LICENSE
                    ----------------------------

                            2006-Jan-27

                    Copyright 1996-2002, 2006 by
          David Turner, Robert Wilhelm, and Werner Lemberg



Introduction
============

  The FreeType  Project is distributed in  several archive packages;
  some of them may contain, in addition to the FreeType font engine,
  various tools and  contributions which rely on, or  relate to, the
  FreeType Project.

  This  license applies  to all  files found  in such  packages, and
  which do not  fall under their own explicit  license.  The license
  affects  thus  the  FreeType   font  engine,  the  test  programs,
  documentation and makefiles, at the very least.

  This  license   was  inspired  by  the  BSD,   Artistic,  and  IJG
  (Independent JPEG  Group) licenses, which  all encourage inclusion
  and  use of  free  software in  commercial  and freeware  products
  alike.  As a consequence, its main points are that:

    o We don't promise that this software works. However, we will be
      interested in any kind of bug reports. (\`as is' distribution)

    o You can  use this software for whatever you  want, in parts or
      full form, without having to pay us. (\`royalty-free' usage)

    o You may not pretend that  you wrote this software.  If you use
      it, or  only parts of it,  in a program,  you must acknowledge
      somewhere  in  your  documentation  that  you  have  used  the
      FreeType code. (\`credits')

  We  specifically  permit  and  encourage  the  inclusion  of  this
  software, with  or without modifications,  in commercial products.
  We  disclaim  all warranties  covering  The  FreeType Project  and
  assume no liability related to The FreeType Project.


  Finally,  many  people  asked  us  for  a  preferred  form  for  a
  credit/disclaimer to use in compliance with this license.  We thus
  encourage you to use the following text:

   """
    Portions of this software are copyright © <year> The FreeType
    Project (www.freetype.org).  All rights reserved.
   """

  Please replace <year> with the value from the FreeType version you
  actually use.


Legal Terms
===========

0. Definitions
--------------

  Throughout this license,  the terms \`package', \`FreeType Project',
  and  \`FreeType  archive' refer  to  the  set  of files  originally
  distributed  by the  authors  (David Turner,  Robert Wilhelm,  and
  Werner Lemberg) as the \`FreeType Project', be they named as alpha,
  beta or final release.

  \`You' refers to  the licensee, or person using  the project, where
  \`using' is a generic term including compiling the project's source
  code as  well as linking it  to form a  \`program' or \`executable'.
  This  program is  referred to  as  \`a program  using the  FreeType
  engine'.

  This  license applies  to all  files distributed  in  the original
  FreeType  Project,   including  all  source   code,  binaries  and
  documentation,  unless  otherwise  stated   in  the  file  in  its
  original, unmodified form as  distributed in the original archive.
  If you are  unsure whether or not a particular  file is covered by
  this license, you must contact us to verify this.

  The FreeType  Project is copyright (C) 1996-2000  by David Turner,
  Robert Wilhelm, and Werner Lemberg.  All rights reserved except as
  specified below.

1. No Warranty
--------------

  THE FREETYPE PROJECT  IS PROVIDED \`AS IS' WITHOUT  WARRANTY OF ANY
  KIND, EITHER  EXPRESS OR IMPLIED,  INCLUDING, BUT NOT  LIMITED TO,
  WARRANTIES  OF  MERCHANTABILITY   AND  FITNESS  FOR  A  PARTICULAR
  PURPOSE.  IN NO EVENT WILL ANY OF THE AUTHORS OR COPYRIGHT HOLDERS
  BE LIABLE  FOR ANY DAMAGES CAUSED  BY THE USE OR  THE INABILITY TO
  USE, OF THE FREETYPE PROJECT.

2. Redistribution
-----------------

  This  license  grants  a  worldwide, royalty-free,  perpetual  and
  irrevocable right  and license to use,  execute, perform, compile,
  display,  copy,   create  derivative  works   of,  distribute  and
  sublicense the  FreeType Project (in  both source and  object code
  forms)  and  derivative works  thereof  for  any  purpose; and  to
  authorize others  to exercise  some or all  of the  rights granted
  herein, subject to the following conditions:

    o Redistribution of  source code  must retain this  license file
      (\`FTL.TXT') unaltered; any  additions, deletions or changes to
      the original  files must be clearly  indicated in accompanying
      documentation.   The  copyright   notices  of  the  unaltered,
      original  files must  be  preserved in  all  copies of  source
      files.

    o Redistribution in binary form must provide a  disclaimer  that
      states  that  the software is based in part of the work of the
      FreeType Team,  in  the  distribution  documentation.  We also
      encourage you to put an URL to the FreeType web page  in  your
      documentation, though this isn't mandatory.

  These conditions  apply to any  software derived from or  based on
  the FreeType Project,  not just the unmodified files.   If you use
  our work, you  must acknowledge us.  However, no  fee need be paid
  to us.

3. Advertising
--------------

  Neither the  FreeType authors and  contributors nor you  shall use
  the name of the  other for commercial, advertising, or promotional
  purposes without specific prior written permission.

  We suggest,  but do not require, that  you use one or  more of the
  following phrases to refer  to this software in your documentation
  or advertising  materials: \`FreeType Project',  \`FreeType Engine',
  \`FreeType library', or \`FreeType Distribution'.

  As  you have  not signed  this license,  you are  not  required to
  accept  it.   However,  as  the FreeType  Project  is  copyrighted
  material, only  this license, or  another one contracted  with the
  authors, grants you  the right to use, distribute,  and modify it.
  Therefore,  by  using,  distributing,  or modifying  the  FreeType
  Project, you indicate that you understand and accept all the terms
  of this license.

4. Contacts
-----------

  There are two mailing lists related to FreeType:

    o freetype@nongnu.org

      Discusses general use and applications of FreeType, as well as
      future and  wanted additions to the  library and distribution.
      If  you are looking  for support,  start in  this list  if you
      haven't found anything to help you in the documentation.

    o freetype-devel@nongnu.org

      Discusses bugs,  as well  as engine internals,  design issues,
      specific licenses, porting, etc.

  Our home page can be found at

    https://www.freetype.org


--- end of FTL.TXT ---
EOF
)

cwe=$(cat << EOF
# Terms of Use
CWE™ is free to use by any organization or individual for any research, 
development, and/or commercial purposes, per these CWE Terms of Use. 
Accordingly, The MITRE Corporation hereby grants you a non-exclusive, 
royalty-free license to use CWE for research, development, and commercial purposes.
Any copy you make for such purposes is authorized on the condition that 
you reproduce MITRE's copyright designation and this license in any such copy. 
CWE is a trademark of The MITRE Corporation. Please contact cwe@mitre.org 
if you require further clarification on this issue.

## Disclaimers
By accessing information through this site you (as “the user”) hereby agrees 
the site and the information is provided on an “as is” basis only without 
warranty of any kind, express or implied, including but not limited to 
implied warranties of merchantability, availability, accuracy, noninfringement, 
or fitness for a particular purpose. Use of this site and the information 
is at the user's own risk. The user shall comply with all applicable laws, 
rules, and regulations, and the data source's restrictions, when using the site.

By contributing information to this site you (as “the contributor”) hereby 
represents and warrants the contributor has obtained all necessary permissions 
from copyright holders and other third parties to allow the contributor to contribute, 
and this site to host and display, the information and any such contribution, 
hosting, and displaying will not violate any law, rule, or regulation. 
Additionally, the contributor hereby grants all users of such information a perpetual,
worldwide, non-exclusive, no-charge, royalty-free, irrevocable license to reproduce, 
prepare derivative works of, publicly display, publicly perform, sublicense, 
and distribute such information and all derivative works.

The MITRE Corporation expressly disclaims any liability for any damages arising 
from the contributor's contribution of such information, the user's use of the 
site or such information, and The MITRE Corporation's hosting the tool and 
displaying the information. The foregoing disclaimer specifically includes 
but is not limited to general, consequential, indirect, incidental, exemplary, 
or special or punitive damages (including but not limited to loss of income, 
program interruption, loss of information, or other pecuniary loss) 
arising out of use of this information, no matter the cause of action, 
even if The MITRE Corporation has been advised of the possibility of such damages.
EOF
)

randomcolor=$(cat << EOF
MIT License

Copyright (c) 2016 Kevin Wu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
)

attrs=$(cat << EOF
The MIT License (MIT)

Copyright (c) 2015 Hynek Schlawack and the attrs contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
)

referencing=$(cat << EOF
MIT License

Copyright (c) 2018 raimon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
)

typing_extensions=$(cat << EOF
A. HISTORY OF THE SOFTWARE
==========================

Python was created in the early 1990s by Guido van Rossum at Stichting
Mathematisch Centrum (CWI, see https://www.cwi.nl) in the Netherlands
as a successor of a language called ABC.  Guido remains Python's
principal author, although it includes many contributions from others.

In 1995, Guido continued his work on Python at the Corporation for
National Research Initiatives (CNRI, see https://www.cnri.reston.va.us)
in Reston, Virginia where he released several versions of the
software.

In May 2000, Guido and the Python core development team moved to
BeOpen.com to form the BeOpen PythonLabs team.  In October of the same
year, the PythonLabs team moved to Digital Creations, which became
Zope Corporation.  In 2001, the Python Software Foundation (PSF, see
https://www.python.org/psf/) was formed, a non-profit organization
created specifically to own Python-related Intellectual Property.
Zope Corporation was a sponsoring member of the PSF.

All Python releases are Open Source (see https://opensource.org for
the Open Source Definition).  Historically, most, but not all, Python
releases have also been GPL-compatible; the table below summarizes
the various releases.

    Release         Derived     Year        Owner       GPL-
                    from                                compatible? (1)

    0.9.0 thru 1.2              1991-1995   CWI         yes
    1.3 thru 1.5.2  1.2         1995-1999   CNRI        yes
    1.6             1.5.2       2000        CNRI        no
    2.0             1.6         2000        BeOpen.com  no
    1.6.1           1.6         2001        CNRI        yes (2)
    2.1             2.0+1.6.1   2001        PSF         no
    2.0.1           2.0+1.6.1   2001        PSF         yes
    2.1.1           2.1+2.0.1   2001        PSF         yes
    2.1.2           2.1.1       2002        PSF         yes
    2.1.3           2.1.2       2002        PSF         yes
    2.2 and above   2.1.1       2001-now    PSF         yes

Footnotes:

(1) GPL-compatible doesn't mean that we're distributing Python under
    the GPL.  All Python licenses, unlike the GPL, let you distribute
    a modified version without making your changes open source.  The
    GPL-compatible licenses make it possible to combine Python with
    other software that is released under the GPL; the others don't.

(2) According to Richard Stallman, 1.6.1 is not GPL-compatible,
    because its license has a choice of law clause.  According to
    CNRI, however, Stallman's lawyer has told CNRI's lawyer that 1.6.1
    is "not incompatible" with the GPL.

Thanks to the many outside volunteers who have worked under Guido's
direction to make these releases possible.


B. TERMS AND CONDITIONS FOR ACCESSING OR OTHERWISE USING PYTHON
===============================================================

Python software and documentation are licensed under the
Python Software Foundation License Version 2.

Starting with Python 3.8.6, examples, recipes, and other code in
the documentation are dual licensed under the PSF License Version 2
and the Zero-Clause BSD license.

Some software incorporated into Python is under different licenses.
The licenses are listed with code falling under that license.


PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation;
All Rights Reserved" are retained in Python alone or in any derivative version
prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.


BEOPEN.COM LICENSE AGREEMENT FOR PYTHON 2.0
-------------------------------------------

BEOPEN PYTHON OPEN SOURCE LICENSE AGREEMENT VERSION 1

1. This LICENSE AGREEMENT is between BeOpen.com ("BeOpen"), having an
office at 160 Saratoga Avenue, Santa Clara, CA 95051, and the
Individual or Organization ("Licensee") accessing and otherwise using
this software in source or binary form and its associated
documentation ("the Software").

2. Subject to the terms and conditions of this BeOpen Python License
Agreement, BeOpen hereby grants Licensee a non-exclusive,
royalty-free, world-wide license to reproduce, analyze, test, perform
and/or display publicly, prepare derivative works, distribute, and
otherwise use the Software alone or in any derivative version,
provided, however, that the BeOpen Python License is retained in the
Software, alone or in any derivative version prepared by Licensee.

3. BeOpen is making the Software available to Licensee on an "AS IS"
basis.  BEOPEN MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, BEOPEN MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

4. BEOPEN SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF THE
SOFTWARE FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS
AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THE SOFTWARE, OR ANY
DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

5. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

6. This License Agreement shall be governed by and interpreted in all
respects by the law of the State of California, excluding conflict of
law provisions.  Nothing in this License Agreement shall be deemed to
create any relationship of agency, partnership, or joint venture
between BeOpen and Licensee.  This License Agreement does not grant
permission to use BeOpen trademarks or trade names in a trademark
sense to endorse or promote products or services of Licensee, or any
third party.  As an exception, the "BeOpen Python" logos available at
http://www.pythonlabs.com/logos.html may be used according to the
permissions granted on that web page.

7. By copying, installing or otherwise using the software, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.


CNRI LICENSE AGREEMENT FOR PYTHON 1.6.1
---------------------------------------

1. This LICENSE AGREEMENT is between the Corporation for National
Research Initiatives, having an office at 1895 Preston White Drive,
Reston, VA 20191 ("CNRI"), and the Individual or Organization
("Licensee") accessing and otherwise using Python 1.6.1 software in
source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, CNRI
hereby grants Licensee a nonexclusive, royalty-free, world-wide
license to reproduce, analyze, test, perform and/or display publicly,
prepare derivative works, distribute, and otherwise use Python 1.6.1
alone or in any derivative version, provided, however, that CNRI's
License Agreement and CNRI's notice of copyright, i.e., "Copyright (c)
1995-2001 Corporation for National Research Initiatives; All Rights
Reserved" are retained in Python 1.6.1 alone or in any derivative
version prepared by Licensee.  Alternately, in lieu of CNRI's License
Agreement, Licensee may substitute the following text (omitting the
quotes): "Python 1.6.1 is made available subject to the terms and
conditions in CNRI's License Agreement.  This Agreement together with
Python 1.6.1 may be located on the internet using the following
unique, persistent identifier (known as a handle): 1895.22/1013.  This
Agreement may also be obtained from a proxy server on the internet
using the following URL: http://hdl.handle.net/1895.22/1013".

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python 1.6.1 or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python 1.6.1.

4. CNRI is making Python 1.6.1 available to Licensee on an "AS IS"
basis.  CNRI MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, CNRI MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON 1.6.1 WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. CNRI SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
1.6.1 FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 1.6.1,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. This License Agreement shall be governed by the federal
intellectual property law of the United States, including without
limitation the federal copyright law, and, to the extent such
U.S. federal law does not apply, by the law of the Commonwealth of
Virginia, excluding Virginia's conflict of law provisions.
Notwithstanding the foregoing, with regard to derivative works based
on Python 1.6.1 that incorporate non-separable material that was
previously distributed under the GNU General Public License (GPL), the
law of the Commonwealth of Virginia shall govern this License
Agreement only as to issues arising under or with respect to
Paragraphs 4, 5, and 7 of this License Agreement.  Nothing in this
License Agreement shall be deemed to create any relationship of
agency, partnership, or joint venture between CNRI and Licensee.  This
License Agreement does not grant permission to use CNRI trademarks or
trade name in a trademark sense to endorse or promote products or
services of Licensee, or any third party.

8. By clicking on the "ACCEPT" button where indicated, or by copying,
installing or otherwise using Python 1.6.1, Licensee agrees to be
bound by the terms and conditions of this License Agreement.

        ACCEPT


CWI LICENSE AGREEMENT FOR PYTHON 0.9.0 THROUGH 1.2
--------------------------------------------------

Copyright (c) 1991 - 1995, Stichting Mathematisch Centrum Amsterdam,
The Netherlands.  All rights reserved.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the name of Stichting Mathematisch
Centrum or CWI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

ZERO-CLAUSE BSD LICENSE FOR CODE IN THE PYTHON DOCUMENTATION
----------------------------------------------------------------------

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
EOF
)

pytest_asyncio=$(cat << EOF
Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "{}"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright {yyyy} {name of copyright owner}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
EOF
)

pillow=$(cat << EOF
The Python Imaging Library (PIL) is

    Copyright © 1997-2011 by Secret Labs AB
    Copyright © 1995-2011 by Fredrik Lundh and contributors

Pillow is the friendly PIL fork. It is

    Copyright © 2010 by Jeffrey A. Clark and contributors

Like PIL, Pillow is licensed under the open source MIT-CMU License:

By obtaining, using, and/or copying this software and/or its associated
documentation, you agree that you have read, understood, and will comply
with the following terms and conditions:

Permission to use, copy, modify and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appears in all copies, and that
both that copyright notice and this permission notice appear in supporting
documentation, and that the name of Secret Labs AB or the author not be
used in advertising or publicity pertaining to distribution of the software
without specific, written prior permission.

SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.
IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
EOF
)

urllib3=$(cat << EOF
MIT License

Copyright (c) 2008-2020 Andrey Petrov and contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
)

pikepdf=$(cat << EOF
Mozilla Public License Version 2.0
==================================

1. Definitions
--------------

1.1. "Contributor"
    means each individual or legal entity that creates, contributes to
    the creation of, or owns Covered Software.

1.2. "Contributor Version"
    means the combination of the Contributions of others (if any) used
    by a Contributor and that particular Contributor's Contribution.

1.3. "Contribution"
    means Covered Software of a particular Contributor.

1.4. "Covered Software"
    means Source Code Form to which the initial Contributor has attached
    the notice in Exhibit A, the Executable Form of such Source Code
    Form, and Modifications of such Source Code Form, in each case
    including portions thereof.

1.5. "Incompatible With Secondary Licenses"
    means

    (a) that the initial Contributor has attached the notice described
        in Exhibit B to the Covered Software; or

    (b) that the Covered Software was made available under the terms of
        version 1.1 or earlier of the License, but not also under the
        terms of a Secondary License.

1.6. "Executable Form"
    means any form of the work other than Source Code Form.

1.7. "Larger Work"
    means a work that combines Covered Software with other material, in
    a separate file or files, that is not Covered Software.

1.8. "License"
    means this document.

1.9. "Licensable"
    means having the right to grant, to the maximum extent possible,
    whether at the time of the initial grant or subsequently, any and
    all of the rights conveyed by this License.

1.10. "Modifications"
    means any of the following:

    (a) any file in Source Code Form that results from an addition to,
        deletion from, or modification of the contents of Covered
        Software; or

    (b) any new file in Source Code Form that contains any Covered
        Software.

1.11. "Patent Claims" of a Contributor
    means any patent claim(s), including without limitation, method,
    process, and apparatus claims, in any patent Licensable by such
    Contributor that would be infringed, but for the grant of the
    License, by the making, using, selling, offering for sale, having
    made, import, or transfer of either its Contributions or its
    Contributor Version.

1.12. "Secondary License"
    means either the GNU General Public License, Version 2.0, the GNU
    Lesser General Public License, Version 2.1, the GNU Affero General
    Public License, Version 3.0, or any later versions of those
    licenses.

1.13. "Source Code Form"
    means the form of the work preferred for making modifications.

1.14. "You" (or "Your")
    means an individual or a legal entity exercising rights under this
    License. For legal entities, "You" includes any entity that
    controls, is controlled by, or is under common control with You. For
    purposes of this definition, "control" means (a) the power, direct
    or indirect, to cause the direction or management of such entity,
    whether by contract or otherwise, or (b) ownership of more than
    fifty percent (50%) of the outstanding shares or beneficial
    ownership of such entity.

2. License Grants and Conditions
--------------------------------

2.1. Grants

Each Contributor hereby grants You a world-wide, royalty-free,
non-exclusive license:

(a) under intellectual property rights (other than patent or trademark)
    Licensable by such Contributor to use, reproduce, make available,
    modify, display, perform, distribute, and otherwise exploit its
    Contributions, either on an unmodified basis, with Modifications, or
    as part of a Larger Work; and

(b) under Patent Claims of such Contributor to make, use, sell, offer
    for sale, have made, import, and otherwise transfer either its
    Contributions or its Contributor Version.

2.2. Effective Date

The licenses granted in Section 2.1 with respect to any Contribution
become effective for each Contribution on the date the Contributor first
distributes such Contribution.

2.3. Limitations on Grant Scope

The licenses granted in this Section 2 are the only rights granted under
this License. No additional rights or licenses will be implied from the
distribution or licensing of Covered Software under this License.
Notwithstanding Section 2.1(b) above, no patent license is granted by a
Contributor:

(a) for any code that a Contributor has removed from Covered Software;
    or

(b) for infringements caused by: (i) Your and any other third party's
    modifications of Covered Software, or (ii) the combination of its
    Contributions with other software (except as part of its Contributor
    Version); or

(c) under Patent Claims infringed by Covered Software in the absence of
    its Contributions.

This License does not grant any rights in the trademarks, service marks,
or logos of any Contributor (except as may be necessary to comply with
the notice requirements in Section 3.4).

2.4. Subsequent Licenses

No Contributor makes additional grants as a result of Your choice to
distribute the Covered Software under a subsequent version of this
License (see Section 10.2) or under the terms of a Secondary License (if
permitted under the terms of Section 3.3).

2.5. Representation

Each Contributor represents that the Contributor believes its
Contributions are its original creation(s) or it has sufficient rights
to grant the rights to its Contributions conveyed by this License.

2.6. Fair Use

This License is not intended to limit any rights You have under
applicable copyright doctrines of fair use, fair dealing, or other
equivalents.

2.7. Conditions

Sections 3.1, 3.2, 3.3, and 3.4 are conditions of the licenses granted
in Section 2.1.

3. Responsibilities
-------------------

3.1. Distribution of Source Form

All distribution of Covered Software in Source Code Form, including any
Modifications that You create or to which You contribute, must be under
the terms of this License. You must inform recipients that the Source
Code Form of the Covered Software is governed by the terms of this
License, and how they can obtain a copy of this License. You may not
attempt to alter or restrict the recipients' rights in the Source Code
Form.

3.2. Distribution of Executable Form

If You distribute Covered Software in Executable Form then:

(a) such Covered Software must also be made available in Source Code
    Form, as described in Section 3.1, and You must inform recipients of
    the Executable Form how they can obtain a copy of such Source Code
    Form by reasonable means in a timely manner, at a charge no more
    than the cost of distribution to the recipient; and

(b) You may distribute such Executable Form under the terms of this
    License, or sublicense it under different terms, provided that the
    license for the Executable Form does not attempt to limit or alter
    the recipients' rights in the Source Code Form under this License.

3.3. Distribution of a Larger Work

You may create and distribute a Larger Work under terms of Your choice,
provided that You also comply with the requirements of this License for
the Covered Software. If the Larger Work is a combination of Covered
Software with a work governed by one or more Secondary Licenses, and the
Covered Software is not Incompatible With Secondary Licenses, this
License permits You to additionally distribute such Covered Software
under the terms of such Secondary License(s), so that the recipient of
the Larger Work may, at their option, further distribute the Covered
Software under the terms of either this License or such Secondary
License(s).

3.4. Notices

You may not remove or alter the substance of any license notices
(including copyright notices, patent notices, disclaimers of warranty,
or limitations of liability) contained within the Source Code Form of
the Covered Software, except that You may alter any license notices to
the extent required to remedy known factual inaccuracies.

3.5. Application of Additional Terms

You may choose to offer, and to charge a fee for, warranty, support,
indemnity or liability obligations to one or more recipients of Covered
Software. However, You may do so only on Your own behalf, and not on
behalf of any Contributor. You must make it absolutely clear that any
such warranty, support, indemnity, or liability obligation is offered by
You alone, and You hereby agree to indemnify every Contributor for any
liability incurred by such Contributor as a result of warranty, support,
indemnity or liability terms You offer. You may include additional
disclaimers of warranty and limitations of liability specific to any
jurisdiction.

4. Inability to Comply Due to Statute or Regulation
---------------------------------------------------

If it is impossible for You to comply with any of the terms of this
License with respect to some or all of the Covered Software due to
statute, judicial order, or regulation then You must: (a) comply with
the terms of this License to the maximum extent possible; and (b)
describe the limitations and the code they affect. Such description must
be placed in a text file included with all distributions of the Covered
Software under this License. Except to the extent prohibited by statute
or regulation, such description must be sufficiently detailed for a
recipient of ordinary skill to be able to understand it.

5. Termination
--------------

5.1. The rights granted under this License will terminate automatically
if You fail to comply with any of its terms. However, if You become
compliant, then the rights granted under this License from a particular
Contributor are reinstated (a) provisionally, unless and until such
Contributor explicitly and finally terminates Your grants, and (b) on an
ongoing basis, if such Contributor fails to notify You of the
non-compliance by some reasonable means prior to 60 days after You have
come back into compliance. Moreover, Your grants from a particular
Contributor are reinstated on an ongoing basis if such Contributor
notifies You of the non-compliance by some reasonable means, this is the
first time You have received notice of non-compliance with this License
from such Contributor, and You become compliant prior to 30 days after
Your receipt of the notice.

5.2. If You initiate litigation against any entity by asserting a patent
infringement claim (excluding declaratory judgment actions,
counter-claims, and cross-claims) alleging that a Contributor Version
directly or indirectly infringes any patent, then the rights granted to
You by any and all Contributors for the Covered Software under Section
2.1 of this License shall terminate.

5.3. In the event of termination under Sections 5.1 or 5.2 above, all
end user license agreements (excluding distributors and resellers) which
have been validly granted by You or Your distributors under this License
prior to termination shall survive termination.

************************************************************************
*                                                                      *
*  6. Disclaimer of Warranty                                           *
*  -------------------------                                           *
*                                                                      *
*  Covered Software is provided under this License on an "as is"       *
*  basis, without warranty of any kind, either expressed, implied, or  *
*  statutory, including, without limitation, warranties that the       *
*  Covered Software is free of defects, merchantable, fit for a        *
*  particular purpose or non-infringing. The entire risk as to the     *
*  quality and performance of the Covered Software is with You.        *
*  Should any Covered Software prove defective in any respect, You     *
*  (not any Contributor) assume the cost of any necessary servicing,   *
*  repair, or correction. This disclaimer of warranty constitutes an   *
*  essential part of this License. No use of any Covered Software is   *
*  authorized under this License except under this disclaimer.         *
*                                                                      *
************************************************************************

************************************************************************
*                                                                      *
*  7. Limitation of Liability                                          *
*  --------------------------                                          *
*                                                                      *
*  Under no circumstances and under no legal theory, whether tort      *
*  (including negligence), contract, or otherwise, shall any           *
*  Contributor, or anyone who distributes Covered Software as          *
*  permitted above, be liable to You for any direct, indirect,         *
*  special, incidental, or consequential damages of any character      *
*  including, without limitation, damages for lost profits, loss of    *
*  goodwill, work stoppage, computer failure or malfunction, or any    *
*  and all other commercial damages or losses, even if such party      *
*  shall have been informed of the possibility of such damages. This   *
*  limitation of liability shall not apply to liability for death or   *
*  personal injury resulting from such party's negligence to the       *
*  extent applicable law prohibits such limitation. Some               *
*  jurisdictions do not allow the exclusion or limitation of           *
*  incidental or consequential damages, so this exclusion and          *
*  limitation may not apply to You.                                    *
*                                                                      *
************************************************************************

8. Litigation
-------------

Any litigation relating to this License may be brought only in the
courts of a jurisdiction where the defendant maintains its principal
place of business and such litigation shall be governed by laws of that
jurisdiction, without reference to its conflict-of-law provisions.
Nothing in this Section shall prevent a party's ability to bring
cross-claims or counter-claims.

9. Miscellaneous
----------------

This License represents the complete agreement concerning the subject
matter hereof. If any provision of this License is held to be
unenforceable, such provision shall be reformed only to the extent
necessary to make it enforceable. Any law or regulation which provides
that the language of a contract shall be construed against the drafter
shall not be used to construe this License against a Contributor.

10. Versions of the License
---------------------------

10.1. New Versions

Mozilla Foundation is the license steward. Except as provided in Section
10.3, no one other than the license steward has the right to modify or
publish new versions of this License. Each version will be given a
distinguishing version number.

10.2. Effect of New Versions

You may distribute the Covered Software under the terms of the version
of the License under which You originally received the Covered Software,
or under the terms of any subsequent version published by the license
steward.

10.3. Modified Versions

If you create software not governed by this License, and you want to
create a new license for such software, you may create and use a
modified version of this License if you rename the license and remove
any references to the name of the license steward (except to note that
such modified license differs from this License).

10.4. Distributing Source Code Form that is Incompatible With Secondary
Licenses

If You choose to distribute Source Code Form that is Incompatible With
Secondary Licenses under the terms of this version of the License, the
notice described in Exhibit B of this License must be attached.

Exhibit A - Source Code Form License Notice
-------------------------------------------

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

If it is not possible or desirable to put the notice in a particular
file, then You may include the notice in a location (such as a LICENSE
file in a relevant directory) where a recipient would be likely to look
for such a notice.

You may add additional accurate notices of copyright ownership.

Exhibit B - "Incompatible With Secondary Licenses" Notice
---------------------------------------------------------

  This Source Code Form is "Incompatible With Secondary Licenses", as
  defined by the Mozilla Public License, v. 2.0.
EOF
)

for pkg in $ignore
do
  echo "" >> NOTICE  # Add newline
  echo "$pkg" >> NOTICE  # Add package name
  pkg_license=$(echo "$pkg" | tr '-' '_')
  echo "${!pkg_license}" >> NOTICE  # Add license contents
done
