# Ant Design Style Guide

## Setup (App Router)

```typescript
// app/providers.tsx
'use client';

import { ConfigProvider } from 'antd';

const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
  },
};

export function Providers({ children }: { children: React.ReactNode }) {
  return <ConfigProvider theme={theme}>{children}</ConfigProvider>;
}
```

## Component Mapping

| HTML Element | Ant Design Component |
|--------------|---------------------|
| `<div>` | `<div>` or layout components |
| `<button>` | `<Button>` |
| `<input>` | `<Input>` |
| `<form>` | `<Form>` |
| Flex container | `<Flex>` or `<Space>` |
| Grid container | `<Row>` + `<Col>` |

## Layout Components

```tsx
// Flex/Space
<Space direction="vertical" size="middle">
  <div>Item 1</div>
  <div>Item 2</div>
</Space>

<Flex gap="middle" justify="space-between" align="center">
  <div>Left</div>
  <div>Right</div>
</Flex>

// Grid (24 columns)
<Row gutter={[16, 16]}>
  <Col xs={24} md={12} lg={8}>
    <Card>Content</Card>
  </Col>
  <Col xs={24} md={12} lg={8}>
    <Card>Content</Card>
  </Col>
</Row>
```

## Form Components

```tsx
<Form
  form={form}
  layout="vertical"
  onFinish={handleSubmit}
>
  <Form.Item
    label="Email"
    name="email"
    rules={[
      { required: true, message: 'Email is required' },
      { type: 'email', message: 'Invalid email' },
    ]}
  >
    <Input placeholder="you@example.com" />
  </Form.Item>

  <Form.Item
    label="Role"
    name="role"
    rules={[{ required: true }]}
  >
    <Select>
      <Select.Option value="user">User</Select.Option>
      <Select.Option value="admin">Admin</Select.Option>
    </Select>
  </Form.Item>

  <Form.Item
    label="Bio"
    name="bio"
  >
    <Input.TextArea rows={4} />
  </Form.Item>

  <Form.Item>
    <Button type="primary" htmlType="submit">
      Submit
    </Button>
  </Form.Item>
</Form>
```

## Button Types

```tsx
<Button type="primary">Primary</Button>
<Button>Default</Button>
<Button type="dashed">Dashed</Button>
<Button type="text">Text</Button>
<Button type="link">Link</Button>
<Button danger>Danger</Button>
<Button type="primary" loading>Loading</Button>
```

## Modal Pattern

```tsx
import { Modal } from 'antd';

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal
        title="Title"
        open={open}
        onOk={handleOk}
        onCancel={() => setOpen(false)}
        okText="Confirm"
        cancelText="Cancel"
      >
        <p>Modal content</p>
      </Modal>
    </>
  );
}

// Quick modals
Modal.confirm({
  title: 'Are you sure?',
  content: 'This action cannot be undone.',
  onOk: () => handleDelete(),
});
```

## Message & Notification

```tsx
import { message, notification } from 'antd';

// Quick messages (toast)
message.success('Operation completed');
message.error('Something went wrong');
message.loading('Processing...');

// Notifications (more detailed)
notification.success({
  message: 'Success',
  description: 'Your changes have been saved.',
});
```

## Table Component

```tsx
const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: 'Email',
    dataIndex: 'email',
    key: 'email',
  },
  {
    title: 'Actions',
    key: 'actions',
    render: (_, record) => (
      <Space>
        <Button type="link" onClick={() => handleEdit(record)}>
          Edit
        </Button>
        <Button type="link" danger onClick={() => handleDelete(record)}>
          Delete
        </Button>
      </Space>
    ),
  },
];

<Table
  dataSource={data}
  columns={columns}
  rowKey="id"
  pagination={{ pageSize: 10 }}
/>
```

## Card Component

```tsx
<Card
  title="Card Title"
  extra={<Button type="link">More</Button>}
  actions={[
    <EditOutlined key="edit" />,
    <DeleteOutlined key="delete" />,
  ]}
>
  <Card.Meta
    avatar={<Avatar src={user.avatar} />}
    title={user.name}
    description={user.email}
  />
</Card>
```

## Key Rules

1. Use Form.Item with rules for validation
2. Use message for quick feedback, notification for detailed
3. Use Modal.confirm() for quick confirmations
4. Use ConfigProvider for theming
5. Grid is 24 columns (not 12 like Bootstrap)
6. Use Space/Flex for simple layouts
7. Always provide rowKey for Table
8. Use type="primary" for main actions
