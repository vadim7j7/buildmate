# Mantine UI Style Guide

## Overview

Use Mantine v7+ components for all UI. Never use raw HTML when a Mantine component exists.

## Component Mapping

| Raw HTML | Use Instead |
|----------|-------------|
| `<button>` | `<Button>` |
| `<input>` | `<TextInput>`, `<NumberInput>`, etc. |
| `<select>` | `<Select>` |
| `<form>` | `<form>` with Mantine form hooks |
| `<table>` | `<Table>` |
| `<div>` for layout | `<Stack>`, `<Group>`, `<Flex>`, `<Grid>` |
| `<div>` for card | `<Card>`, `<Paper>` |
| `<span>` for text | `<Text>` |
| `<h1>`-`<h6>` | `<Title order={n}>` |

## Layout Components

```tsx
// Vertical stack with gap
<Stack gap="md">
  <Component1 />
  <Component2 />
</Stack>

// Horizontal group with gap
<Group gap="sm">
  <Button>Action 1</Button>
  <Button>Action 2</Button>
</Group>

// Responsive grid
<Grid>
  <Grid.Col span={{ base: 12, md: 6 }}>
    <Content />
  </Grid.Col>
</Grid>
```

## Form Handling

Use `@mantine/form` for all forms:

```tsx
import { useForm } from '@mantine/form';

const form = useForm({
  initialValues: {
    email: '',
    password: '',
  },
  validate: {
    email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
    password: (value) => (value.length >= 8 ? null : 'Password too short'),
  },
});

<form onSubmit={form.onSubmit(handleSubmit)}>
  <TextInput {...form.getInputProps('email')} label="Email" />
  <PasswordInput {...form.getInputProps('password')} label="Password" />
  <Button type="submit">Submit</Button>
</form>
```

## Notifications

Use `@mantine/notifications` for all user feedback:

```tsx
import { notifications } from '@mantine/notifications';

notifications.show({
  title: 'Success',
  message: 'Your changes have been saved',
  color: 'green',
});
```

## Modals

Use `@mantine/modals` for confirmations and dialogs:

```tsx
import { modals } from '@mantine/modals';

modals.openConfirmModal({
  title: 'Delete item?',
  children: <Text>This action cannot be undone.</Text>,
  labels: { confirm: 'Delete', cancel: 'Cancel' },
  confirmProps: { color: 'red' },
  onConfirm: () => deleteItem(),
});
```

## Theming

Access theme values via hooks, never hardcode colors:

```tsx
import { useMantineTheme } from '@mantine/core';

const theme = useMantineTheme();
// Use theme.colors.blue[6] instead of '#228be6'
```

## Loading States

Use Mantine loading components:

```tsx
<LoadingOverlay visible={isLoading} />
<Skeleton height={50} visible={isLoading} />
<Button loading={isSubmitting}>Submit</Button>
```
