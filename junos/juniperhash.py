#
#
# JuniperHash builds a nested hash out of a juniper
# configuration file.
#
# Converted by ChatGPT from the following Ruby Script:
#  https://raw.githubusercontent.com/sventantau/juniper_hash/master/juniper_hash.rb
#
# Usage: (Ruby instructions, needs to be tested with Python version)
# require 'juniper_hash'
# hash_config = JuniperHash.get_hash(File.open('juniper.conf').read)
# text_config = JuniperHash.build_config_from_hash(hash_config)
# JuniperHash.get_hash(text_config) == hash_config
# => true
#
#
#  Copyright (C) 2015, Sven Tantau <sven@beastiebytes.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining
#  a copy of this software and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#import re

class JuniperHash:
    @staticmethod
    def get_hash(content_string):
        lines_array = content_string.split("\n")
        comment_free_lines_array = [x for x in lines_array if not x.startswith('#')]
        return JuniperHash.format_blocks_to_hash(comment_free_lines_array)

    @staticmethod
    def build_config_from_hash(block, name=None, level=0):
        indent = '  ' * level
        out = ''
        if name:
            out = indent + name + " {\n"
            level += 1
        indent = '  ' * level
        for key, value in block.items():
            if isinstance(value, str) and not value:
                out += indent + key + ";\n"
            elif isinstance(value, str):
                out += indent + key + ' ' + value + ";\n"
            elif isinstance(value, list):
                for v in value:
                    out += indent + key + ' ' + v + ";\n"
            elif isinstance(value, dict):
                out += JuniperHash.build_config_from_hash(value, key, level)
        if name:
            level -= 1
            indent = '  ' * level
            out += indent + "}\n"
        return out

    @staticmethod
    def extract_key_value_from_line(line):
        comment = None
        #print(f"Raw Line: {line}")
        # Check if "## SECRET-DATA" is present at the end of the line
        if line.endswith("## SECRET-DATA"):
            line = line[:-len("## SECRET-DATA")].strip()
        line = line.strip()
        if "##" in line:
            print(f"COMMENT: {line}")
            #line.strip("'")
            parts = line.split('##')
            key = "COMMENT"
            if len(parts[0]) > 0:
                key = parts[0].strip()
            #else:
            if len(parts[1]) > 0:
                value = parts[1].strip()

        if ((comment is not None) and (len(comment) == 0)):
            comment = None
        #if comment != None:
        #    print(f"WARN: {key} {comment}")

        if " " not in line:
            key = line.split(';')[0]
            value = "True"
            return key, value
        else:
            if line.endswith(";"):
                key, value = line.split(' ', 1)
                key, value = key.strip(), value.strip(";")
                if '"' in value:
                    #value = re.findall(r'"([^"]*)"', string)
                    value.strip('"')
                    #print(f"\tFound Double Quotes {value}")
                return key, value
            else:
                #print(f"Processing line {line}")
                key, value = line.split(' ', 1)
                key, value = key.strip(), value.strip()

        #if "## Last commit:" in line:
        #    return "last_commit", value

        #if line.startswith("#"):
        #    return None

        if value:
            return key, value[:-1]
        else:
            return key[:-1], ''

    @staticmethod
    def extract_blocks_from_block(lines_array):
        output = {}
        brace_depth = 0
        target_found = False
        block_name = None

        for line in lines_array:
            if not line.strip():
                continue
            # fill array with lines to store a new block
            if target_found:
                output[block_name].append(line)

            if '{' in line:
                brace_depth += 1
            if '}' in line:
                brace_depth -= 1

            if brace_depth == 1 and not target_found:
                # found a block
                block_name = line.split('{')[0].strip()
                output[block_name] = []
                target_found = True

            if brace_depth == 0:
                if '}' not in line:
                    # 'key value' row found
                    key, value = JuniperHash.extract_key_value_from_line(line)
                    if key in output:
                        if isinstance(output[key], list):
                            output[key].append(value)
                        else:
                            # transform to array
                            output[key] = [output[key], value]
                    else:
                        output[key] = value
                target_found = False

        return output

    # build the hash (main function)
    @staticmethod
    def format_blocks_to_hash(lines_array, key=None):
        out = {}
        if not isinstance(lines_array, list):
            return lines_array
        if '{' not in ''.join(lines_array) and '}' not in ''.join(lines_array):
            return lines_array
        blocks = JuniperHash.extract_blocks_from_block(lines_array)
        for bkey, l_array in blocks.items():
            out[bkey] = JuniperHash.format_blocks_to_hash(l_array, bkey)
        return out
