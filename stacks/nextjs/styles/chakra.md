# Chakra UI Style Guide

## Setup (App Router)

```typescript
// app/providers.tsx
'use client';

import { ChakraProvider, extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
}
```

## Component Mapping

| HTML Element | Chakra Component |
|--------------|------------------|
| `<div>` | `<Box>` |
| `<span>` | `<Text as="span">` |
| `<button>` | `<Button>` |
| `<input>` | `<Input>` |
| `<form>` | `<form>` (use FormControl for fields) |
| `<img>` | `<Image>` (from next/image preferred) |
| Flex container | `<Flex>` or `<HStack>` / `<VStack>` |
| Grid container | `<Grid>` / `<SimpleGrid>` |

## Layout Components

```tsx
// Flex layouts
<HStack spacing={4}>
  <Box>Item 1</Box>
  <Box>Item 2</Box>
</HStack>

<VStack align="stretch" spacing={4}>
  <Box>Item 1</Box>
  <Box>Item 2</Box>
</VStack>

// Grid
<SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
  <Box>Card 1</Box>
  <Box>Card 2</Box>
  <Box>Card 3</Box>
</SimpleGrid>

// Container with max width
<Container maxW="container.lg" py={8}>
  {children}
</Container>
```

## Form Components

```tsx
<FormControl isRequired isInvalid={!!errors.email}>
  <FormLabel>Email</FormLabel>
  <Input
    type="email"
    {...register('email')}
    placeholder="you@example.com"
  />
  <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
</FormControl>

<FormControl>
  <FormLabel>Role</FormLabel>
  <Select {...register('role')}>
    <option value="user">User</option>
    <option value="admin">Admin</option>
  </Select>
</FormControl>
```

## Button Variants

```tsx
<Button colorScheme="brand">Primary</Button>
<Button colorScheme="brand" variant="outline">Secondary</Button>
<Button colorScheme="gray" variant="ghost">Ghost</Button>
<Button colorScheme="red" variant="solid">Danger</Button>
<Button isLoading loadingText="Saving...">Save</Button>
```

## Responsive Props

```tsx
// Array syntax: [mobile, tablet, desktop]
<Box
  p={[2, 4, 6]}
  fontSize={['sm', 'md', 'lg']}
  display={['none', 'block']}
/>

// Object syntax
<Box
  p={{ base: 2, md: 4, lg: 6 }}
  fontSize={{ base: 'sm', md: 'lg' }}
/>
```

## Styling Props

```tsx
<Box
  bg="gray.100"
  _dark={{ bg: 'gray.800' }}
  p={4}
  borderRadius="md"
  boxShadow="sm"
  _hover={{ boxShadow: 'md' }}
>
  Content
</Box>
```

## Modal Pattern

```tsx
import { useDisclosure } from '@chakra-ui/react';

function MyComponent() {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <>
      <Button onClick={onOpen}>Open Modal</Button>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Title</ModalHeader>
          <ModalCloseButton />
          <ModalBody>Content</ModalBody>
          <ModalFooter>
            <Button onClick={onClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
```

## Toast Notifications

```tsx
import { useToast } from '@chakra-ui/react';

function MyComponent() {
  const toast = useToast();

  const handleSuccess = () => {
    toast({
      title: 'Success',
      description: 'Operation completed.',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
}
```

## Key Rules

1. Use style props instead of CSS/className
2. Use semantic color tokens (gray.100, brand.500)
3. Use responsive array/object syntax
4. Use useDisclosure for modals/drawers
5. Use useToast for notifications
6. Wrap forms with FormControl for validation states
