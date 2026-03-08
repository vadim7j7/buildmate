import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Edit3,
  FileText,
  FolderOpen,
  ListChecks,
  Plus,
  Save,
  Trash2,
  X,
} from 'lucide-react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import { useResizablePanel } from '../hooks/useResizablePanel'
import { ResizeHandle } from './ResizeHandle'
import type { Document, TaskDoc } from '../types'

export function DocsPanel() {
  const { state, toggleDocs, refreshDocs } = useDashboard()
  const { documents } = state
  const { handleResizeStart } = useResizablePanel('stack')

  // Selected document state
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [selectedTaskDoc, setSelectedTaskDoc] = useState<TaskDoc | null>(null)

  // Edit state
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editFolder, setEditFolder] = useState('')

  // Create state
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newFolder, setNewFolder] = useState('')

  // Task docs
  const [taskDocs, setTaskDocs] = useState<TaskDoc[]>([])

  // Folder collapse state
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set())
  const [collapsedTaskGroups, setCollapsedTaskGroups] = useState<Set<string>>(new Set())
  const [taskFolderCollapsed, setTaskFolderCollapsed] = useState(false)

  // Saving state
  const [saving, setSaving] = useState(false)

  // Load task docs on mount
  useEffect(() => {
    api.getTaskResultDocs().then(setTaskDocs).catch(() => {})
  }, [])

  // Group documents by folder
  const grouped = useMemo(() => {
    const map = new Map<string, Document[]>()
    for (const doc of documents) {
      const folder = doc.folder || '(ungrouped)'
      if (!map.has(folder)) map.set(folder, [])
      map.get(folder)!.push(doc)
    }
    return map
  }, [documents])

  // Group task artifacts by task title
  const taskDocsByTask = useMemo(() => {
    const map = new Map<string, TaskDoc[]>()
    for (const td of taskDocs) {
      const key = td.task_title || '(unknown task)'
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(td)
    }
    return map
  }, [taskDocs])

  const selectedDoc = documents.find(d => d.id === selectedDocId)

  const toggleTaskGroup = (taskTitle: string) => {
    setCollapsedTaskGroups(prev => {
      const next = new Set(prev)
      if (next.has(taskTitle)) next.delete(taskTitle)
      else next.add(taskTitle)
      return next
    })
  }

  const toggleFolder = (folder: string) => {
    setCollapsedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folder)) next.delete(folder)
      else next.add(folder)
      return next
    })
  }

  const handleSelectDoc = (doc: Document) => {
    setSelectedDocId(doc.id)
    setSelectedTaskDoc(null)
    setIsEditing(false)
    setShowCreateForm(false)
  }

  const handleSelectTaskDoc = (td: TaskDoc) => {
    setSelectedTaskDoc(td)
    setSelectedDocId(null)
    setIsEditing(false)
    setShowCreateForm(false)
  }

  const startEditing = () => {
    if (!selectedDoc) return
    setEditTitle(selectedDoc.title)
    setEditContent(selectedDoc.content)
    setEditFolder(selectedDoc.folder)
    setIsEditing(true)
  }

  const cancelEditing = () => {
    setIsEditing(false)
  }

  const handleSave = useCallback(async () => {
    if (!selectedDocId) return
    setSaving(true)
    try {
      await api.updateDocument(selectedDocId, {
        title: editTitle,
        content: editContent,
        folder: editFolder,
      })
      await refreshDocs()
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to save document:', err)
    } finally {
      setSaving(false)
    }
  }, [selectedDocId, editTitle, editContent, editFolder, refreshDocs])

  const handleDelete = async () => {
    if (!selectedDocId) return
    try {
      await api.deleteDocument(selectedDocId)
      setSelectedDocId(null)
      await refreshDocs()
    } catch (err) {
      console.error('Failed to delete document:', err)
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    setSaving(true)
    try {
      const doc = await api.createDocument(newTitle.trim(), newContent, newFolder.trim())
      await refreshDocs()
      setShowCreateForm(false)
      setNewTitle('')
      setNewContent('')
      setNewFolder('')
      setSelectedDocId(doc.id)
      setSelectedTaskDoc(null)
    } catch (err) {
      console.error('Failed to create document:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveTaskDoc = async (td: TaskDoc, folder: string) => {
    try {
      const doc = await api.saveFromTask(td.id, td.label, td.content, folder)
      await refreshDocs()
      setSelectedDocId(doc.id)
      setSelectedTaskDoc(null)
    } catch (err) {
      console.error('Failed to save task doc:', err)
    }
  }

  return (
    <div className="w-full border-l border-surface-800/50 bg-surface-900/95 backdrop-blur-md flex flex-col h-full animate-slide-in-right relative">
      <ResizeHandle onMouseDown={handleResizeStart} />

      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-800/50">
        <div className="flex items-center gap-2.5">
          <FileText className="w-4.5 h-4.5 text-blue-400" />
          <h2 className="text-sm font-semibold text-gray-100">Docs</h2>
          <span className="ml-auto px-2 py-0.5 rounded-md bg-surface-800/80 text-xs text-gray-400">
            {documents.length}
          </span>
          <button
            onClick={() => { setShowCreateForm(true); setSelectedDocId(null); setSelectedTaskDoc(null) }}
            className="p-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-surface-800 transition-colors"
            title="New document"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={toggleDocs}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: folder tree */}
        <div className="w-48 flex-shrink-0 border-r border-surface-800/50 overflow-y-auto">
          <div className="py-2">
            {/* User doc folders */}
            {[...grouped.entries()].map(([folder, docs]) => (
              <div key={folder}>
                <button
                  onClick={() => toggleFolder(folder)}
                  className="w-full flex items-center gap-1.5 px-3 py-1.5 text-left hover:bg-surface-800/50 transition-colors"
                >
                  {collapsedFolders.has(folder)
                    ? <ChevronRight className="w-3 h-3 text-gray-600 flex-shrink-0" />
                    : <ChevronDown className="w-3 h-3 text-gray-600 flex-shrink-0" />
                  }
                  <FolderOpen className="w-3 h-3 text-blue-400/60 flex-shrink-0" />
                  <span className="text-[11px] text-gray-400 truncate flex-1">
                    {folder}
                  </span>
                  <span className="text-[10px] text-gray-600 flex-shrink-0">{docs.length}</span>
                </button>
                {!collapsedFolders.has(folder) && (
                  <div className="ml-3.5">
                    {docs.map(doc => (
                      <button
                        key={doc.id}
                        onClick={() => handleSelectDoc(doc)}
                        className={`
                          w-full flex items-center gap-1.5 px-3 py-1 text-left transition-colors
                          ${selectedDocId === doc.id
                            ? 'bg-blue-500/10 text-blue-300'
                            : 'text-gray-400 hover:bg-surface-800/50 hover:text-gray-300'
                          }
                        `}
                      >
                        <FileText className="w-3 h-3 flex-shrink-0 opacity-50" />
                        <span className="text-[11px] truncate">{doc.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Task artifacts grouped by task */}
            {taskDocs.length > 0 && (
              <div>
                <button
                  onClick={() => setTaskFolderCollapsed(!taskFolderCollapsed)}
                  className="w-full flex items-center gap-1.5 px-3 py-1.5 text-left hover:bg-surface-800/50 transition-colors mt-1 border-t border-surface-800/30 pt-2"
                >
                  {taskFolderCollapsed
                    ? <ChevronRight className="w-3 h-3 text-gray-600 flex-shrink-0" />
                    : <ChevronDown className="w-3 h-3 text-gray-600 flex-shrink-0" />
                  }
                  <ListChecks className="w-3 h-3 text-emerald-400/60 flex-shrink-0" />
                  <span className="text-[11px] text-gray-400 truncate flex-1">Artifacts</span>
                  <span className="text-[10px] text-gray-600 flex-shrink-0">{taskDocs.length}</span>
                </button>
                {!taskFolderCollapsed && (
                  <div className="ml-1.5">
                    {[...taskDocsByTask.entries()].map(([taskTitle, artifacts]) => (
                      <div key={taskTitle}>
                        <button
                          onClick={() => toggleTaskGroup(taskTitle)}
                          className="w-full flex items-center gap-1.5 px-3 py-1 text-left hover:bg-surface-800/50 transition-colors"
                        >
                          {collapsedTaskGroups.has(taskTitle)
                            ? <ChevronRight className="w-3 h-3 text-gray-600 flex-shrink-0" />
                            : <ChevronDown className="w-3 h-3 text-gray-600 flex-shrink-0" />
                          }
                          <FolderOpen className="w-3 h-3 text-emerald-400/60 flex-shrink-0" />
                          <span className="text-[11px] text-gray-400 truncate flex-1">{taskTitle}</span>
                          <span className="text-[10px] text-gray-600 flex-shrink-0">{artifacts.length}</span>
                        </button>
                        {!collapsedTaskGroups.has(taskTitle) && (
                          <div className="ml-3.5">
                            {artifacts.map(td => (
                              <button
                                key={td.id}
                                onClick={() => handleSelectTaskDoc(td)}
                                className={`
                                  w-full flex items-center gap-1.5 px-3 py-1 text-left transition-colors
                                  ${selectedTaskDoc?.id === td.id
                                    ? 'bg-emerald-500/10 text-emerald-300'
                                    : 'text-gray-400 hover:bg-surface-800/50 hover:text-gray-300'
                                  }
                                `}
                              >
                                <FileText className="w-3 h-3 flex-shrink-0 opacity-50" />
                                <span className="text-[11px] truncate">{td.label}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {documents.length === 0 && taskDocs.length === 0 && (
              <div className="px-3 py-6 text-center">
                <FileText className="w-6 h-6 text-gray-700 mx-auto mb-2" />
                <p className="text-[11px] text-gray-600">No documents yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: document view or create form */}
        <div className="flex-1 overflow-y-auto">
          {showCreateForm ? (
            <CreateForm
              title={newTitle}
              content={newContent}
              folder={newFolder}
              saving={saving}
              onTitleChange={setNewTitle}
              onContentChange={setNewContent}
              onFolderChange={setNewFolder}
              onSave={handleCreate}
              onCancel={() => setShowCreateForm(false)}
            />
          ) : selectedDoc ? (
            isEditing ? (
              <EditView
                title={editTitle}
                content={editContent}
                folder={editFolder}
                saving={saving}
                onTitleChange={setEditTitle}
                onContentChange={setEditContent}
                onFolderChange={setEditFolder}
                onSave={handleSave}
                onCancel={cancelEditing}
              />
            ) : (
              <DocView
                doc={selectedDoc}
                onEdit={startEditing}
                onDelete={handleDelete}
              />
            )
          ) : selectedTaskDoc ? (
            <TaskDocView taskDoc={selectedTaskDoc} onSave={handleSaveTaskDoc} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <FileText className="w-8 h-8 mb-3 opacity-40" />
              <p className="text-sm">Select a document</p>
              <p className="text-xs mt-1 text-gray-600">or create a new one</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// --- Sub-components ---

function DocView({
  doc,
  onEdit,
  onDelete,
}: {
  doc: Document
  onEdit: () => void
  onDelete: () => void
}) {
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-white flex-1 min-w-0 truncate">{doc.title}</h3>
        {doc.folder && (
          <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-[10px] text-blue-400 border border-blue-500/20 flex-shrink-0">
            {doc.folder}
          </span>
        )}
        <button
          onClick={onEdit}
          className="p-1.5 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-surface-800 transition-colors flex-shrink-0"
          title="Edit"
        >
          <Edit3 className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onDelete}
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors flex-shrink-0"
          title="Delete"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="artifact-markdown text-sm">
        <Markdown remarkPlugins={[remarkGfm]}>{doc.content || '*No content*'}</Markdown>
      </div>
    </div>
  )
}

function TaskDocView({
  taskDoc,
  onSave,
}: {
  taskDoc: TaskDoc
  onSave: (td: TaskDoc, folder: string) => void
}) {
  const [saveFolder, setSaveFolder] = useState('')
  const [showSave, setShowSave] = useState(false)

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-white flex-1 min-w-0 truncate">{taskDoc.label}</h3>
        <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-[10px] text-emerald-400 border border-emerald-500/20 flex-shrink-0">
          {taskDoc.artifact_type}
        </span>
        <button
          onClick={() => setShowSave(!showSave)}
          className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] text-blue-400 hover:bg-blue-500/10 transition-colors flex-shrink-0"
        >
          <Save className="w-3 h-3" /> Save to Docs
        </button>
      </div>
      <p className="text-[10px] text-gray-500 mb-2 truncate" title={taskDoc.file_path}>
        From: {taskDoc.task_title}
      </p>
      {showSave && (
        <div className="mb-3 flex items-center gap-2 p-2 bg-surface-850 rounded-lg border border-surface-700/50">
          <input
            value={saveFolder}
            onChange={e => setSaveFolder(e.target.value)}
            placeholder="Folder (optional)"
            className="flex-1 bg-transparent text-xs text-gray-200 placeholder-gray-500 outline-none"
          />
          <button
            onClick={() => { onSave(taskDoc, saveFolder.trim()); setShowSave(false) }}
            className="px-2 py-1 text-[11px] font-medium bg-blue-600 text-white rounded-md hover:bg-blue-500 transition-colors"
          >
            Save
          </button>
        </div>
      )}
      <div className="artifact-markdown text-sm">
        <Markdown remarkPlugins={[remarkGfm]}>{taskDoc.content || '*No content*'}</Markdown>
      </div>
    </div>
  )
}

function EditView({
  title,
  content,
  folder,
  saving,
  onTitleChange,
  onContentChange,
  onFolderChange,
  onSave,
  onCancel,
}: {
  title: string
  content: string
  folder: string
  saving: boolean
  onTitleChange: (v: string) => void
  onContentChange: (v: string) => void
  onFolderChange: (v: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  const [showPreview, setShowPreview] = useState(false)

  return (
    <div className="p-4 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-3">
        <input
          value={title}
          onChange={e => onTitleChange(e.target.value)}
          className="flex-1 bg-surface-850 border border-surface-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
          placeholder="Document title"
        />
        <input
          value={folder}
          onChange={e => onFolderChange(e.target.value)}
          className="w-32 bg-surface-850 border border-surface-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
          placeholder="Folder"
        />
      </div>
      <div className="flex items-center gap-1 mb-2 bg-surface-800 rounded-lg p-0.5 self-start">
        <button
          onClick={() => setShowPreview(false)}
          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
            !showPreview ? 'bg-surface-700 text-white' : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Write
        </button>
        <button
          onClick={() => setShowPreview(true)}
          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
            showPreview ? 'bg-surface-700 text-white' : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Preview
        </button>
      </div>
      <div className="flex-1 min-h-0">
        {showPreview ? (
          <div className="h-full overflow-y-auto bg-surface-850 border border-surface-700 rounded-lg p-3 artifact-markdown text-sm">
            <Markdown remarkPlugins={[remarkGfm]}>{content || '*No content*'}</Markdown>
          </div>
        ) : (
          <textarea
            value={content}
            onChange={e => onContentChange(e.target.value)}
            className="w-full h-full bg-surface-850 border border-surface-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500/50"
            placeholder="Document content (Markdown supported)"
          />
        )}
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white rounded-lg hover:bg-surface-800 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onSave}
          disabled={!title.trim() || saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50"
        >
          <Save className="w-3 h-3" />
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  )
}

function CreateForm({
  title,
  content,
  folder,
  saving,
  onTitleChange,
  onContentChange,
  onFolderChange,
  onSave,
  onCancel,
}: {
  title: string
  content: string
  folder: string
  saving: boolean
  onTitleChange: (v: string) => void
  onContentChange: (v: string) => void
  onFolderChange: (v: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="p-4 flex flex-col h-full">
      <h3 className="text-sm font-semibold text-white mb-3">New Document</h3>
      <div className="flex items-center gap-2 mb-3">
        <input
          value={title}
          onChange={e => onTitleChange(e.target.value)}
          className="flex-1 bg-surface-850 border border-surface-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
          placeholder="Document title"
          autoFocus
        />
        <input
          value={folder}
          onChange={e => onFolderChange(e.target.value)}
          className="w-32 bg-surface-850 border border-surface-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
          placeholder="Folder"
        />
      </div>
      <div className="flex-1 min-h-0">
        <textarea
          value={content}
          onChange={e => onContentChange(e.target.value)}
          className="w-full h-full bg-surface-850 border border-surface-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500/50"
          placeholder="Document content (Markdown supported)"
        />
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white rounded-lg hover:bg-surface-800 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onSave}
          disabled={!title.trim() || saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50"
        >
          <Plus className="w-3 h-3" />
          {saving ? 'Creating...' : 'Create'}
        </button>
      </div>
    </div>
  )
}
