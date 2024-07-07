const React = require('react');

const mockChakraComponent = (displayName) => {
  const component = ({ children, ...props }) => React.createElement('div', props, children);
  component.displayName = displayName;
  return component;
};

module.exports = {
  Box: mockChakraComponent('Box'),
  VStack: mockChakraComponent('VStack'),
  HStack: mockChakraComponent('HStack'),
  Button: mockChakraComponent('Button'),
  Input: mockChakraComponent('Input'),
  useColorMode: jest.fn(() => ({ colorMode: 'light', toggleColorMode: jest.fn() })),
  Tabs: mockChakraComponent('Tabs'),
  TabList: mockChakraComponent('TabList'),
  TabPanels: mockChakraComponent('TabPanels'),
  Tab: mockChakraComponent('Tab'),
  TabPanel: mockChakraComponent('TabPanel'),
  Text: mockChakraComponent('Text'),
  Modal: mockChakraComponent('Modal'),
  ModalOverlay: mockChakraComponent('ModalOverlay'),
  ModalContent: mockChakraComponent('ModalContent'),
  ModalHeader: mockChakraComponent('ModalHeader'),
  ModalFooter: mockChakraComponent('ModalFooter'),
  ModalBody: mockChakraComponent('ModalBody'),
  ModalCloseButton: mockChakraComponent('ModalCloseButton'),
  useDisclosure: jest.fn(() => ({ isOpen: false, onOpen: jest.fn(), onClose: jest.fn() })),
  Flex: mockChakraComponent('Flex'),
  IconButton: mockChakraComponent('IconButton'),
  Menu: mockChakraComponent('Menu'),
  MenuButton: mockChakraComponent('MenuButton'),
  MenuList: mockChakraComponent('MenuList'),
  MenuItem: mockChakraComponent('MenuItem'),
  InputGroup: mockChakraComponent('InputGroup'),
  Progress: mockChakraComponent('Progress'),
  Textarea: mockChakraComponent('Textarea'),
  Checkbox: mockChakraComponent('Checkbox'),
  ChakraProvider: ({ children }) => children,
};