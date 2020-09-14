class XML:
    def __init__(self, filename=None):
        self.elements_by_id = {}
        self.root = self.__read_xml(filename) if filename else None

    def get_element_by_id(self, id):
        return self.elements_by_id.get(id)

    def get_elements_by_name(self, name):
        elements = []
        self.root.get_elements_by_name(name, elements)
        return elements

    def write(self, filename):
        self.root.write(filename)

    def __parse_tag(self, xml, offset):
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
                    if attrib_name == 'id':
                        self.elements_by_id[attrib_value] = node
                    offset += 1
                    break
                offset += 1

    def __read_xml(self, filename):
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
        return self.__parse_xml(data, start_offset)

    def __parse_xml(self, xml, offset=0, parent_node=None):
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
                node, offset, self_enclosed, end_tag = self.__parse_tag(xml, offset)
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
                        offset = self.__parse_xml(xml, offset, node)
            else:
                if not text_offset:
                    text_offset = offset
                offset += 1


class XMLParseError(Exception):
    pass


def ignore_white_space(file, offset):
    while True:
        if file[offset] not in (' ', '\n', '\t'):
            return offset
        offset += 1


class XMLNode:
    def __init__(self, tag, text=None, id=None, name=None, parent=None, xml=None):
        self.children = []
        self.attributes = {}
        if id:
            self.attributes['id'] = id
            if xml:
                xml.elements_by_id[id] = self
        if name:
            self.attributes['name'] = name
        self.text = text
        self.tag = tag
        if parent:
            parent.add_child(self)

    def __str__(self):
        tag = self.tag
        if self.attributes:
            tag += ' ' + str(self.attributes)
        return tag

    def __iter__(self):
        return iter(self.children)

    def __next__(self):
        return next(self.children)

    def get_id(self):
        return self.attributes.get('id')

    def get_name(self):
        return self.attributes.get('name')

    def __getitem__(self, item):
        for x in self.children:
            if x.tag == item:
                return x

    def get_referenced_id(self, attribute):
        attribute = self.attributes[attribute]
        if attribute:
            return attribute[1:]

    def get_elements_by_tag(self, tag):
        ret = []
        for x in self.children:
            if x.tag == tag:
                ret.append(x)
        return ret

    def get_elements_by_name(self, name, element_list):
        my_name = self.attributes.get('name')
        if my_name == name:
            element_list.append(self)
        for child in self.children:
            child.get_elements_by_name(name, element_list)

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
                my_str = x.get_xml(my_str, indent + '  ')
            my_str += indent + '</' + self.tag + '>\n'
            return my_str
        if not self.text:
            my_str += indent + '<' + self.tag + attrib + '/>\n'
            return my_str
        else:
            my_str += indent + '<' + self.tag + attrib + '>' + str(self.text) + '</' + self.tag + '>\n'
            return my_str

    def get_children(self):
        return self.children

    def get_children_by_element(self, tag):
        ret = []
        for x in self.children:
            if x.tag == tag:
                ret.append(x)
        return ret

    def add_child(self, xmlnode):
        self.children.append(xmlnode)
