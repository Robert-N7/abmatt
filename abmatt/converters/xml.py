class XMLParseError(Exception):
    pass


def ignore_white_space(file, offset):
    while True:
        if file[offset] not in (' ', '\n', '\t'):
            return offset
        offset += 1


def parse_tag(xml, offset):
    start_offset = offset
    if xml[offset] == '/':
        end_tag = True
        start_offset += 1
        offset += 1
    else:
        end_tag = False
    self_enclosed = False
    while True:  # tag name
        char = xml[offset]
        if char in (' ', '\n', '\t'):
            node = XMLNode(xml[start_offset:offset])
            break
        elif char == '/':
            node = XMLNode(xml[start_offset:offset])
            self_enclosed = True
            offset += 1
            assert xml[offset] == '>'
            offset += 1
            return node, offset, self_enclosed, end_tag
        elif char == '>':
            node = XMLNode(xml[start_offset:offset])
            offset += 1
            return node, offset, self_enclosed, end_tag
        offset += 1
    offset += 1
    while True:
        offset = ignore_white_space(xml, offset)
        char = xml[offset]
        if char == '/':
            self_enclosed = True
            offset += 1
            assert xml[offset] == '>'
            offset += 1
            return node, offset, self_enclosed, end_tag
        elif char == '>':
            offset += 1
            return node, offset, self_enclosed, end_tag
        start_offset = offset
        offset += 1
        while True:  # parse attrib_name
            char = xml[offset]
            if char == '=':
                attrib_name = xml[start_offset:offset]
                offset += 1
                if xml[offset] != '"':
                    raise XMLParseError('Expected attribute name')
                offset += 1
                break
            offset += 1
        start_offset = offset
        while True:  # parse attrib_value
            char = xml[offset]
            if char == '"':
                attrib_value = xml[start_offset:offset]
                node.attributes[attrib_name] = attrib_value
                offset += 1
                break
            offset += 1


class XMLNode:
    def __init__(self, tag, text=None):
        self.children = []
        self.attributes = {}
        self.text = text
        self.tag = tag

    def __str__(self):
        tag = self.tag
        if self.attributes:
            tag += ' ' + str(self.attributes)
        return tag

    def write(self, filename):
        with open(filename, 'w') as f:
            my_str = '<?xml version="1.0" encoding="utf-8"?>\n'
            my_str = self.get_xml(my_str)
            f.write(my_str)

    def get_xml(self, my_str, indent=''):
        attrib = ''
        att = self.attributes
        if att:
            for x in att:
                attrib += ' ' + x + '=' + '"' + str(att[x]) + '"'
        if self.children:
            my_str += indent + '<' + self.tag + attrib + '>\n'
            for x in self.children:
                my_str = x.get_xml(my_str, indent + '\t')
            my_str += indent + '</' + self.tag + '>\n'
            return my_str
        if not self.text:
            my_str += indent + '<' + self.tag + attrib + '/>\n'
            return my_str
        else:
            my_str += indent + '<' + self.tag + attrib + '>' + str(self.text) + '</' + self.tag + '>\n'
            return my_str

    def get_children_by_element(self, tag):
        ret = []
        for x in self.children:
            if x.tag == tag:
                ret.append(x)
        return ret

    def add_child(self, child_node):
        self.children.append(child_node)


def read_xml(filename):
    with open(filename) as f:
        data = f.read()
    first_element = data.find('<')
    if first_element < 0:
        raise XMLParseError('No elements in xml!')
    start_offset = 0
    if data[first_element + 1: first_element + 5] == '?xml':
        end_first_element = data.find('>', first_element + 5)
        if end_first_element > 0:
            start_offset = end_first_element + 1
    return parse_xml(data, start_offset)


def parse_xml(xml, offset=0, parent_node=None):
    max_offset = len(xml)
    text_offset = 0
    is_root = False
    while offset < max_offset:
        try:
            offset = ignore_white_space(xml, offset)
        except IndexError:
            break
        char = xml[offset]
        if char == '<':
            if text_offset:
                text = xml[text_offset:offset]
                if not parent_node:
                    raise XMLParseError('Found text outside tags {}'.format(text))
                parent_node.text = text
            offset += 1
            node, offset, self_enclosed, end_tag = parse_tag(xml, offset)
            if not parent_node:
                if end_tag:
                    raise XMLParseError('No Matching start tag for {}'.format(node))
                elif self_enclosed:  # no parent and self_enclosed = done
                    return node
                parent_node = node
                is_root = True
            elif end_tag:
                if node.tag != parent_node.tag:
                    raise XMLParseError('Expected end tag for {}, not {}'.format(parent_node, node))
                return offset if not is_root else parent_node
            else:  # not end tag and has parent
                parent_node.children.append(node)
                if not self_enclosed:
                    offset = parse_xml(xml, offset, node)
        else:
            if not text_offset:
                text_offset = offset
            offset += 1
