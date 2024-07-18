import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Box, Input, VStack, Text, useColorMode } from '@chakra-ui/react';

const API_URL = 'http://127.0.0.1:8000';

interface TerminalLine {
  content: string;
  isCommand: boolean;
}

const Console: React.FC = () => {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<TerminalLine[]>([]);
  const [currentDirectory, setCurrentDirectory] = useState('');
  const { colorMode } = useColorMode();
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCurrentDirectory();
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [history]);

  const fetchCurrentDirectory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/console/cwd`);
      setCurrentDirectory(response.data.cwd);
    } catch (error) {
      console.error('Error fetching current directory:', error);
      addToHistory('Error fetching current directory', false);
    }
  };

  const addToHistory = (content: string, isCommand: boolean) => {
    setHistory(prev => [...prev, { content, isCommand }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    addToHistory(`${currentDirectory}$ ${input}`, true);
    
    if (input.trim().toLowerCase() === 'clear') {
      setHistory([]);
      setInput('');
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/console/execute`, { command: input });
      if (response.data.result) {
        addToHistory(response.data.result, false);
      }
      if (response.data.cwd) {
        setCurrentDirectory(response.data.cwd);
      }
    } catch (error) {
      console.error('Error executing command:', error);
      addToHistory('Error executing command. Please check the console for details.', false);
    }

    setInput('');
  };

  return (
    <VStack spacing={4} align="stretch" height="100%">
      <Box
        ref={terminalRef}
        bg={colorMode === 'dark' ? 'gray.800' : 'gray.100'}
        color={colorMode === 'dark' ? 'white' : 'black'}
        p={4}
        borderRadius="md"
        height="calc(80vh - 200px)"
        overflowY="auto"
        fontFamily="monospace"
        whiteSpace="pre-wrap"
        textAlign="left"
      >
        {history.map((line, index) => (
          <Text key={index} fontWeight={line.isCommand ? 'bold' : 'normal'}>
            {line.content}
          </Text>
        ))}
      </Box>
      <form onSubmit={handleSubmit}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`${currentDirectory}$ `}
          bg={colorMode === 'dark' ? 'gray.700' : 'white'}
          color={colorMode === 'dark' ? 'white' : 'black'}
        />
      </form>
    </VStack>
  );
};

export default Console;