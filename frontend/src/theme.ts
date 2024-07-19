import { extendTheme, ThemeConfig } from "@chakra-ui/react";
import { StyleFunctionProps } from "@chakra-ui/theme-tools";

const config: ThemeConfig = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  styles: {
    global: (props: StyleFunctionProps) => ({
      body: {
        bg: props.colorMode === "dark" ? "gray.800" : "white",
        color: props.colorMode === "dark" ? "white" : "gray.800",
      }
    })
  },
  components: {
    Button: {
      baseStyle: (props: StyleFunctionProps) => ({
        bg: props.colorMode === "dark" ? "gray.700" : "gray.600", // Changed to dark grey
        color: 'white',
        _hover: {
          bg: props.colorMode === "dark" ? "gray.600" : "gray.500", // Slightly lighter on hover
        },
      }),
    },
    Input: {
      baseStyle: (props: StyleFunctionProps) => ({
        field: {
          bg: props.colorMode === "dark" ? "gray.700" : "white",
          color: props.colorMode === "dark" ? "white" : "gray.800",
        },
      }),
    },
    // Add other components if needed
  }
});

export default theme;