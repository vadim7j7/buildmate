# Material UI (MUI) Style Guide

## Setup (App Router)

```typescript
// app/providers.tsx
'use client';

import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
```

## Component Mapping

| HTML Element | MUI Component |
|--------------|---------------|
| `<div>` | `<Box>` |
| `<span>` | `<Typography component="span">` |
| `<button>` | `<Button>` |
| `<input>` | `<TextField>` |
| `<form>` | `<form>` (use FormControl for structure) |
| Flex container | `<Stack>` or `<Box display="flex">` |
| Grid container | `<Grid container>` |

## Layout Components

```tsx
// Stack (flex column by default)
<Stack spacing={2} direction="row">
  <Item>Item 1</Item>
  <Item>Item 2</Item>
</Stack>

// Grid system (12 columns)
<Grid container spacing={2}>
  <Grid item xs={12} md={6} lg={4}>
    <Card>Content</Card>
  </Grid>
  <Grid item xs={12} md={6} lg={4}>
    <Card>Content</Card>
  </Grid>
</Grid>

// Container
<Container maxWidth="lg">
  {children}
</Container>
```

## Form Components

```tsx
<TextField
  label="Email"
  type="email"
  fullWidth
  required
  error={!!errors.email}
  helperText={errors.email?.message}
  {...register('email')}
/>

<FormControl fullWidth error={!!errors.role}>
  <InputLabel>Role</InputLabel>
  <Select label="Role" {...register('role')}>
    <MenuItem value="user">User</MenuItem>
    <MenuItem value="admin">Admin</MenuItem>
  </Select>
  <FormHelperText>{errors.role?.message}</FormHelperText>
</FormControl>

<TextField
  label="Bio"
  multiline
  rows={4}
  fullWidth
  {...register('bio')}
/>
```

## Button Variants

```tsx
<Button variant="contained" color="primary">Primary</Button>
<Button variant="outlined" color="primary">Secondary</Button>
<Button variant="text">Text</Button>
<Button variant="contained" color="error">Danger</Button>
<Button disabled>Disabled</Button>
<LoadingButton loading variant="contained">Save</LoadingButton>
```

## Box sx Prop

```tsx
<Box
  sx={{
    p: 2,
    bgcolor: 'background.paper',
    borderRadius: 1,
    boxShadow: 1,
    '&:hover': {
      boxShadow: 3,
    },
    // Responsive
    width: { xs: '100%', md: '50%' },
  }}
>
  Content
</Box>
```

## Dialog Pattern

```tsx
import { useState } from 'react';

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Dialog</Button>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Title</DialogTitle>
        <DialogContent>
          <DialogContentText>Content here</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleConfirm}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
```

## Snackbar Notifications

```tsx
import { Snackbar, Alert } from '@mui/material';

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <Snackbar
      open={open}
      autoHideDuration={3000}
      onClose={() => setOpen(false)}
    >
      <Alert severity="success" onClose={() => setOpen(false)}>
        Operation completed successfully!
      </Alert>
    </Snackbar>
  );
}
```

## Table Component

```tsx
<TableContainer component={Paper}>
  <Table>
    <TableHead>
      <TableRow>
        <TableCell>Name</TableCell>
        <TableCell>Email</TableCell>
        <TableCell align="right">Actions</TableCell>
      </TableRow>
    </TableHead>
    <TableBody>
      {rows.map((row) => (
        <TableRow key={row.id}>
          <TableCell>{row.name}</TableCell>
          <TableCell>{row.email}</TableCell>
          <TableCell align="right">
            <IconButton><EditIcon /></IconButton>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
</TableContainer>
```

## Key Rules

1. Use `sx` prop for inline styles (not style or className)
2. Use theme spacing units (p: 2 = 16px)
3. Use semantic colors (primary.main, error.light)
4. Use responsive object syntax in sx: { xs: '', md: '' }
5. Import components from '@mui/material'
6. Use TextField for inputs (combines Input + FormControl)
7. Use LoadingButton from '@mui/lab' for async actions
