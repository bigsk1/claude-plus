import React, { useState, useRef } from 'react';
import axios, { AxiosError } from 'axios';
import {
  Box, Input, VStack, Text, useColorMode, Button,
} from '@chakra-ui/react';

const API_URL = 'http://127.0.0.1:8000';

interface ErrorResponse {
  detail: string;
}

const Console: React.FC = () => {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState<string[]>([]);
  const [cwd, setCwd] = useState('');
  const outputRef = useRef<HTMLDivElement>(null);
  const { colorMode } = useColorMode();

  const runCommand = async (command: string) => {
    try {
      const trimmedInput = command.trim();
      setOutput(prev => [...prev, `$ ${trimmedInput}`]);
      
      if (trimmedInput === 'clear') {
        setOutput([]);
      } else {
        const response = await axios.post(`${API_URL}/api/execute`, { command: trimmedInput });
        setOutput(prev => [...prev, response.data.result]);
        if (response.data.cwd) {
          setCwd(response.data.cwd);
        }
      }
    } catch (error) {
      console.error('Error executing command:', error);
      let errorMessage = 'Error executing command. Please check the console for details.';

      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<ErrorResponse>;
        if (axiosError.response) {
          errorMessage = `Error: ${axiosError.response.data.detail || 'Unknown error'}`;
        } else if (axiosError.request) {
          errorMessage = 'Error: No response received from server';
        } else {
          errorMessage = `Error: ${axiosError.message}`;
        }
      }

      setOutput(prev => [...prev, errorMessage]);
    }
    setInput('');
  };

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      await runCommand(input);
    }
  };

  return (
    <VStack spacing={4} align="stretch" height="100%">
      <Box
        ref={outputRef}
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
        {output.map((line, index) => (
          <Text key={index}>{line}</Text>
        ))}
      </Box>
      <Box display="flex">
        <Text mr={2} fontWeight="bold">{cwd}$</Text>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter command (type 'clear' to clear console)"
          flex={1}
        />
      </Box>
      <Box>
        <Button onClick={() => runCommand('python --version')} mr={2}>Python Version</Button>
        <Button onClick={() => runCommand('conda info --envs')} mr={2}>Conda Environments</Button>
        <Button onClick={() => runCommand('pip list')} mr={2}>Installed Packages</Button>
        <Button onClick={() => setOutput([])} colorScheme="red">Clear Console</Button>
      </Box>
    </VStack>
  );
};

export default Console;