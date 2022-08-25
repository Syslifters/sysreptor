#!/bin/bash
set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately

allow_only="MIT"
allow_only="$allow_only;Apache Software License"
allow_only="$allow_only;MIT License"
allow_only="$allow_only;BSD License"
allow_only="$allow_only;GNU General Public License v2 or later (GPLv2+)"
allow_only="$allow_only;GNU Lesser General Public License v2 or later (LGPLv2+)"
allow_only="$allow_only;Mozilla Public License 1.1 (MPL 1.1)"
allow_only="$allow_only;GNU Library or Lesser General Public License (LGPL)"
allow_only="$allow_only;Historical Permission Notice and Disclaimer (HPND)"
allow_only="$allow_only;Mozilla Public License 2.0 (MPL 2.0)Apache Software License"
allow_only="$allow_only;MIT License"
allow_only="$allow_only;BSD License"
allow_only="$allow_only;GNU General Public License v2 or later (GPLv2+)"
allow_only="$allow_only;GNU Lesser General Public License v2 or later (LGPLv2+)"
allow_only="$allow_only;Mozilla Public License 1.1 (MPL 1.1)"
allow_only="$allow_only;GNU Library or Lesser General Public License (LGPL)"
allow_only="$allow_only;Historical Permission Notice and Disclaimer (HPND)"
allow_only="$allow_only;Mozilla Public License 2.0 (MPL 2.0)"

ignore="jsonschema"
ignore="$ignore;webencodings"


virtualenv licenses
source licenses/bin/activate
pip3 install -r requirements.txt
pip3 install pip-licenses
pip-licenses --allow-only "$allow_only" >/dev/null
pip-licenses -l --no-license-path -f plain-vertical --ignore-packages "$ignore" > NOTICE
deactivate

# Those packages do not include valid license files
jsonschema_license='''Copyright (c) 2013 Julian Berman

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
THE SOFTWARE.'''
echo "" >> NOTICE
echo "jsonschema" >> NOTICE
version=`pip freeze | grep jsonschema | cut -d"=" -f 3`
echo "$version" >> NOTICE
echo "MIT License" >> NOTICE
echo "$jsonschema_license" >> NOTICE

webencodings_license='''Copyright (c) 2012 by Simon Sapin.

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
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.'''


echo "" >> NOTICE
echo "webencodings" >> NOTICE
version=`pip freeze | grep webencodings | cut -d"=" -f 3`
echo "$version" >> NOTICE
echo "BSD License" >> NOTICE
echo "$webencodings_license" >> NOTICE

