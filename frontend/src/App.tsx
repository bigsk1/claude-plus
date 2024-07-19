import React, { useState, useEffect, useRef } from 'react';
import {
  Box, VStack, HStack, Button, Input, useColorMode,
  Tabs, TabList, TabPanels, Tab, TabPanel, Text, Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalFooter, ModalBody, ModalCloseButton, useDisclosure, Flex, IconButton,
  Menu, MenuButton, MenuList, MenuItem, InputGroup, Progress, Textarea, useToast
} from '@chakra-ui/react';
import { SunIcon, MoonIcon, ChevronDownIcon, AddIcon, DeleteIcon } from '@chakra-ui/icons';
import { FaImage, FaDownload } from 'react-icons/fa';
import axios from 'axios';
import ReactMarkdown, { Components } from 'react-markdown';
import { ChakraProvider } from '@chakra-ui/react';
import ReactDiffViewer from 'react-diff-viewer-continued';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';


import theme from './theme';
import './App.css';
import FileListing from './FileListing'; 
import Console from './components/Console';
import { FileItem } from './types';

//const API_URL = '/api';
const API_URL = 'http://127.0.0.1:8000';

type MessageType = {
  role: string;
  content: string;
  isHtml?: boolean;
};

type CodeProps = {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  [key: string]: any;
};


function App() {
  const [input, setInput] = useState('');
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [currentDirectory, setCurrentDirectory] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [automodeProgress, setAutomodeProgress] = useState(0);
  const [originalContent, setOriginalContent] = useState('');
  const { colorMode, toggleColorMode } = useColorMode();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  useEffect(() => {
    listFiles(currentDirectory);
  }, [currentDirectory]);

  useEffect(() => {
    scrollToBottom(); // Scroll to bottom whenever messages change
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const formatText = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < lines.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (uploadedFile) {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      try {
        const response = await axios.post(`${API_URL}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const successMessage = `File uploaded: ${uploadedFile.name}`;
        setMessages((prev) => [...prev, { role: 'system', content: successMessage }]);

        // Send the file contents to the chat endpoint
        const chatResponse = await axios.post(`${API_URL}/chat`, {
          message: `File uploaded: ${uploadedFile.name}\n\nContents:\n${response.data.file_contents}`
        });
        setMessages((prev) => [...prev, { role: 'assistant', content: chatResponse.data.response }]);

        listFiles(currentDirectory);
      } catch (error) {
        console.error('Error uploading file:', error);
        let errorMessage = 'Error: Failed to upload file';
        if (axios.isAxiosError(error)) {
          if (error.response) {
            errorMessage += ` - ${error.response.data.detail || error.response.statusText}`;
          } else if (error.request) {
            errorMessage += ' - No response received from server';
          } else {
            errorMessage += ` - ${error.message}`;
          }
        }
        setMessages((prev) => [...prev, { role: 'system', content: errorMessage }]);
      }
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const response = await axios.post(`${API_URL}/analyze_image`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        setMessages((prev) => [...prev, { role: 'assistant', content: `Image Analysis:\n${response.data.analysis}` }]);
      } catch (error) {
        console.error('Error analyzing image:', error);
        let errorMessage = 'Error: Failed to analyze image';
        if (axios.isAxiosError(error) && error.response) {
          errorMessage += ` - ${error.response.data.detail}`;
        }
        setMessages((prev) => [...prev, { role: 'system', content: errorMessage }]);
      }
    }
  };

  const handleAutoMode = async () => {
    if (input.trim()) {
      try {
        setIsAutoMode(true);
        setAutomodeProgress(0);
        setMessages(prev => [...prev, { role: 'user', content: input }]);
        setInput(''); // Clear input field

        const eventSource = new EventSource(`${API_URL}/automode?message=${encodeURIComponent(input)}`);

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.event === 'message') {
            setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
            setAutomodeProgress(prev => Math.min(prev + 20, 100)); // Example progress update
          } else if (data.event === 'end') {
            setAutomodeProgress(100);
            eventSource.close();
            setIsAutoMode(false);
          } else if (data.event === 'error') {
            setMessages(prev => [...prev, { role: 'system', content: data.content }]);
            eventSource.close();
            setIsAutoMode(false);
          }
        };

        eventSource.onerror = (error) => {
          console.error('Error in automode:', error);
          setMessages(prev => [...prev, { role: 'system', content: 'Error: Automode failed' }]);
          eventSource.close();
          setIsAutoMode(false);
        };

        // Cleanup on component unmount
        return () => {
          eventSource.close();
        };
      } catch (error) {
        console.error('Error in automode:', error);
        setMessages(prev => [...prev, { role: 'system', content: 'Error: Automode failed' }]);
      }
    }
  };

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      setMessages((prev) => [...prev, { role: 'user', content: `Searching for: ${searchQuery}`, isHtml: false }]);
      try {
        const response = await axios.post(`${API_URL}/search`, { query: searchQuery });
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response.data.results, isHtml: true }
        ]);
      } catch (error) {
        console.error('Error performing search:', error);
        let errorMessage = 'Error: Failed to perform search';
        if (axios.isAxiosError(error) && error.response) {
          errorMessage += ` - ${error.response.data.detail}`;
        }
        setMessages((prev) => [...prev, { role: 'system', content: errorMessage, isHtml: false }]);
      }
      setSearchQuery('');
    }
  };

  const handleSend = async () => {
    if (input.trim()) {
      setMessages(prev => [...prev, { role: 'user', content: input }]);
      try {
        const response = await axios.post(`${API_URL}/chat`, { message: input });
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: response.data.response }
        ]);
      } catch (error) {
        console.error('Error sending message:', error);
        setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to send message' }]);
      }
      setInput('');
    }
  };

  const listFiles = async (path: string) => {
    try {
      const response = await axios.get(`${API_URL}/list_files`, { params: { path } });
      setFiles(response.data.files || []);
      setCurrentDirectory(response.data.currentDirectory || '');
    } catch (error) {
      console.error('Error listing files:', error);
      setFiles([]);
    }
  };

  const createFolder = async () => {
    const folderName = prompt('Enter folder name:');
    if (folderName) {
      try {
        await axios.post(`${API_URL}/create_folder`, null, { params: { path: `${currentDirectory}/${folderName}` } });
        listFiles(currentDirectory);
      } catch (error) {
        console.error('Error creating folder:', error);
      }
    }
  };

  const createFile = async () => {
    const fileName = prompt('Enter file name:');
    if (fileName) {
      try {
        await axios.post(`${API_URL}/create_file`, null, { params: { path: `${currentDirectory}/${fileName}` } });
        listFiles(currentDirectory);
      } catch (error) {
        console.error('Error creating file:', error);
      }
    }
  };

  const readFile = async (fileName: string) => {
    try {
      const response = await axios.get(`${API_URL}/read_file`, { params: { path: `${currentDirectory}/${fileName}` } });
      setSelectedFile(fileName);
      setFileContent(response.data.content);
      setOriginalContent(response.data.content);
      onOpen();
    } catch (error) {
      console.error('Error reading file:', error);
    }
  };

  const saveFile = async () => {
    try {
      const response = await axios.post(`${API_URL}/write_file`, {
        content: fileContent
      }, {
        params: {
          path: `${currentDirectory}/${selectedFile}`
        }
      });
      alert(response.data.message);  // Show a confirmation message
      onClose();
      listFiles(currentDirectory);
    } catch (error) {
      console.error('Error saving file:', error);
    }
  };

  const deleteFile = async () => {
    if (!selectedFile) {
      alert('Please select a file or folder to delete.');
      return;
    }

    const confirmDelete = window.confirm(`Are you sure you want to delete ${selectedFile}?`);
    if (!confirmDelete) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/delete_file`, {
        params: { path: `${currentDirectory}/${selectedFile}` }
      });
      listFiles(currentDirectory);
      setSelectedFile(''); // Reset selected file after deletion
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('Error deleting file. Please try again.');
    }
  };

  const handleFileClick = (file: FileItem) => {
    if (file.isDirectory) {
      navigateDirectory(file.name);
    } else {
      readFile(file.name);
    }
  };

  const handleSelectFile = (fileName: string) => {
    setSelectedFile(prevSelected => prevSelected === fileName ? null : fileName);
  };

  const navigateDirectory = (dirName: string) => {
    if (dirName === '..') {
      const parentDir = currentDirectory.split('/').slice(0, -1).join('/');
      setCurrentDirectory(parentDir || '.');
    } else {
      setCurrentDirectory(prevDir => prevDir === '.' ? dirName : `${prevDir}/${dirName}`);
    }
    listFiles(dirName === '..' ? currentDirectory.split('/').slice(0, -1).join('/') || '.' : `${currentDirectory}/${dirName}`);
  };

  const createProjectTemplate = async (templateName: string) => {
    try {
      await axios.post(`${API_URL}/create_project`,
        { template: templateName },
        { params: { path: currentDirectory } }
      );
      await listFiles(currentDirectory);  // Refresh the file list
    } catch (error) {
      console.error('Error creating project:', error);
      if (axios.isAxiosError(error) && error.response) {
        console.error('Server response:', error.response.data);
      }
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const viewSetupInstructions = async (fileName: string) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: `The file ${fileName} is located in the directory ${currentDirectory}. Please read this file, then provide detailed information about the file contents for the project containing this file. Include any necessary steps for installing dependencies and executing the code.`
      });
      setMessages(prev => [...prev, { role: 'assistant', content: `Claude: ${response.data.response}` }]);
      setActiveTabIndex(0); // Switch to the chat tab
      onClose(); // Close the modal
    } catch (error) {
      console.error('Error getting setup instructions:', error);
      setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to get setup instructions. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadProjects = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/download_projects`, { 
        responseType: 'blob',
        timeout: 30000 // 30 seconds timeout
      });
      
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'projects.zip');
      document.body.appendChild(link);
      link.click();
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
      window.URL.revokeObjectURL(url);

      toast({
        title: "Download Started",
        description: "Your projects folder is being downloaded.",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error downloading projects:', error);
      toast({
        title: "Download Failed",
        description: "There was an error downloading the projects folder. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const customComponents: Components = {
    code({ inline, className, children, ...props }: CodeProps) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={atomDark}
          language={match[1]}
          PreTag="div"
          showLineNumbers={true}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <Flex direction="column" minHeight="100vh" width="100%" className={colorMode === 'dark' ? 'dark-mode' : 'light-mode'}>
      <Flex as="header" width="100%" justifyContent="space-between" alignItems="center" p={4} bg={colorMode === 'dark' ? 'gray.700' : 'gray.100'}>
        <Text fontSize="2xl" fontWeight="bold">Claude Plus</Text>
        <HStack spacing={4}>
          <IconButton
            icon={<FaDownload />}
            onClick={handleDownloadProjects}
            aria-label="Download Projects"
            title="Download Projects Folder"
          />
          <IconButton
            icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
            onClick={toggleColorMode}
            aria-label="Toggle color mode"
          />
        </HStack>
      </Flex>
      <Flex direction="column" flex={1} p={4} alignItems="center" bg={colorMode === 'dark' ? 'gray.800' : 'white'} color={colorMode === 'dark' ? 'white' : 'gray.800'}>
        <Box width="100%" maxWidth="1200px">
          <Tabs isFitted variant="enclosed" width="100%" index={activeTabIndex} onChange={(index) => setActiveTabIndex(index)}>
            <TabList mb="1em">
              <Tab _selected={{ color: "white", bg: "blue.500" }}>Chat</Tab>
              <Tab _selected={{ color: "white", bg: "blue.500" }}>Files</Tab>
              <Tab _selected={{ color: "white", bg: "blue.500" }}>Console</Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <VStack spacing={4} align="stretch" width="100%">
                  <Box className="chat-box" bg={colorMode === 'dark' ? 'gray.700' : 'gray.200'} borderRadius="md" p={4} height="50vh" overflowY="auto">
                    {messages.map((msg, index) => (
                      <Box
                        key={index}
                        className={`message-box ${msg.isHtml ? 'search-result' : ''}`}
                        mb={2}
                        p={3}
                        borderRadius="md"
                        bg={msg.isHtml ? 'transparent' : (msg.role === 'user' ? (colorMode === 'dark' ? 'blue.600' : 'blue.200') : (colorMode === 'dark' ? 'gray.600' : 'gray.300'))}
                      >
                        {msg.isHtml ? (
                          <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                        ) : (
                          msg.role === 'assistant' ? (
                            <ReactMarkdown
                              children={msg.content}
                              components={customComponents}
                            />
                          ) : formatText(msg.content)
                        )}
                      </Box>
                    ))}
                    <div ref={messagesEndRef} />
                  </Box>
                  <HStack>
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Type your message..."
                      bg={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                    />
                    <Button onClick={handleSend} colorScheme="blue">Send</Button>
                  </HStack>
                  {isAutoMode && (
                    <Progress value={automodeProgress} max={100} width="100%" mt={2} />
                  )}
                  <HStack justifyContent="space-between">
                    <Button onClick={() => fileInputRef.current?.click()} colorScheme="green">
                      Upload File
                    </Button>
                    <Button onClick={handleAutoMode} colorScheme={isAutoMode ? "red" : "yellow"}>
                      {isAutoMode ? 'Deactivate' : 'Activate'} Automode
                    </Button>
                    <Button onClick={clearMessages} colorScheme="red">
                      Clear Chat
                    </Button>
                  </HStack>
                  <HStack justifyContent="space-between">
                    <Menu>
                      <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
                        Create Project
                      </MenuButton>
                      <MenuList>
                        <MenuItem onClick={() => createProjectTemplate('react')}>React App</MenuItem>
                        <MenuItem onClick={() => createProjectTemplate('node')}>Node.js App</MenuItem>
                        <MenuItem onClick={() => createProjectTemplate('python')}>Python App</MenuItem>
                      </MenuList>
                    </Menu>
                    <Button onClick={() => imageInputRef.current?.click()} leftIcon={<FaImage />}>
                      Upload Image
                    </Button>
                  </HStack>
                  <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    onChange={handleFileUpload}
                  />
                  <input
                    type="file"
                    accept="image/*"
                    ref={imageInputRef}
                    style={{ display: 'none' }}
                    onChange={handleImageUpload}
                  />
                </VStack>
                </TabPanel>
              <TabPanel>
                <VStack spacing={4} align="stretch">
                  <HStack justifyContent="space-between">
                    <Text>Files and Folders:</Text>
                    <HStack>
                      <Button onClick={createFolder} leftIcon={<AddIcon />} colorScheme="green">Create Folder</Button>
                      <Button onClick={createFile} leftIcon={<AddIcon />} colorScheme="blue">Create File</Button>
                      <Button onClick={() => listFiles(currentDirectory)} colorScheme="yellow">Refresh</Button>
                      <Button onClick={deleteFile} leftIcon={<DeleteIcon />} colorScheme="red">Delete</Button>
                    </HStack>
                  </HStack>
                  <FileListing 
                    files={files} 
                    onFileClick={handleFileClick}
                    currentDirectory={currentDirectory}
                    selectedFile={selectedFile}
                    onSelectFile={handleSelectFile}
                  />
                </VStack>
              </TabPanel>
                <TabPanel>
                <Console />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      </Flex>
      <Flex as="footer" width="100%" justifyContent="center" p={4} bg={colorMode === 'dark' ? 'gray.700' : 'gray.100'}>
        <Box width="70%">
          <InputGroup size="md" maxWidth="600px" margin="auto">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search the web..."
              bg={colorMode === 'dark' ? 'gray.600' : 'gray.200'}
              pr="4.5rem"
            />
            <Button
              position="absolute"
              right="0"
              top="0"
              h="100%"
              onClick={handleSearch}
            >
              Search
            </Button>
          </InputGroup>
        </Box>
      </Flex>
      <Modal isOpen={isOpen} onClose={onClose} size="6xl">
        <ModalOverlay />
        <ModalContent bg={colorMode === 'dark' ? 'gray.700' : 'white'} maxHeight="90vh">
          <ModalHeader>{selectedFile}</ModalHeader>
          <ModalCloseButton />
          <ModalBody overflowY="auto">
            <ReactDiffViewer
              oldValue={originalContent}
              newValue={fileContent}
              splitView={true}
              disableWordDiff={false}
              styles={{
                variables: {
                  dark: {
                    diffViewerBackground: '#2d3748',
                    diffViewerColor: '#e2e8f0',
                    addedBackground: '#2f4b4d',
                    addedColor: '#e2e8f0',
                    removedBackground: '#4b3534',
                    removedColor: '#e2e8f0',
                    wordAddedBackground: '#044a16',
                    wordRemovedBackground: '#5d0f0f',
                  },
                },
              }}
            />
            <Textarea
              value={fileContent}
              onChange={(e) => setFileContent(e.target.value)}
              height="30vh"
              bg={colorMode === 'dark' ? 'gray.600' : 'white'}
              color={colorMode === 'dark' ? 'white' : 'gray.800'}
              mt={4}
            />
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={saveFile}>
              Save
            </Button>
            <Button
              colorScheme="green"
              mr={3}
              onClick={() => {
                viewSetupInstructions(selectedFile || '');
                onClose();
              }}
              isLoading={isLoading}
              loadingText="Getting Instructions"
            >
              View Setup Instructions
            </Button>
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Flex>
  );
}

export default function AppWithTheme() {
  return (
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  );
}
