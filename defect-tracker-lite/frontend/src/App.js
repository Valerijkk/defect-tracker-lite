import React, { useEffect, useMemo, useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import AppLayout from './components/AppLayout';
import Toaster from './components/Toaster';
import api from './api';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import MenuItem from '@mui/material/MenuItem';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import AttachmentIcon from '@mui/icons-material/Attachment';

const STATUS = ['all','new','in_progress','review','closed','cancelled'];
const STATUS_LABEL = { all:'Все', new:'New', in_progress:'In progress', review:'Review', closed:'Closed', cancelled:'Cancelled' };
const STATUS_COLOR = { new:'info', in_progress:'warning', review:'secondary', closed:'success', cancelled:'default' };
const PRIORITY_COLOR = { low:'default', medium:'primary', high:'error' };

function Login({ onLogged }) {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const submit = async () => {
    try {
      setLoading(true); setError('');
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', data.token);
      localStorage.setItem('role', data.role);
      onLogged();
    } catch {
      setError('Неверный email или пароль');
    } finally { setLoading(false); }
  };
  return (
      <Box sx={{ display:'grid', placeItems:'center', minHeight:'70vh' }}>
        <Paper sx={{ p: 4, width: 420 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>Вход</Typography>
          <Typography variant="body2" color="text.secondary">demo: admin@example.com / admin123</Typography>
          <TextField label="Email" fullWidth sx={{ mt: 2 }} value={email} onChange={e=>setEmail(e.target.value)} />
          <TextField label="Пароль" fullWidth sx={{ mt: 2 }} type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          <Button variant="contained" sx={{ mt: 2 }} fullWidth onClick={submit} disabled={loading}>
            {loading ? <CircularProgress size={20} /> : 'Войти'}
          </Button>
        </Paper>
      </Box>
  );
}

function Dashboard() {
  const role = localStorage.getItem('role');

  const [projects, setProjects] = useState([]);
  const [defects, setDefects] = useState([]);
  const [tab, setTab] = useState(0);
  const [filters, setFilters] = useState({ project_id:'', status:'', priority:'', q:'' });
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ open:false, msg:'', severity:'success' });
  const [dialogDefect, setDialogDefect] = useState(false);
  const [dialogProject, setDialogProject] = useState(false);
  const [newDefect, setNewDefect] = useState({ project_id:'', title:'', description:'', priority:'medium', file:null });
  const [newProject, setNewProject] = useState({ name:'', description:'' });

  const load = async () => {
    setLoading(true);
    try {
      const [p, d] = await Promise.all([api.get('/projects'), api.get('/defects')]);
      setProjects(p.data); setDefects(d.data);
    } finally { setLoading(false); }
  };
  useEffect(()=>{ load(); }, []);

  const filtered = useMemo(() => {
    const st = STATUS[tab];
    return defects.filter(d =>
        (filters.project_id ? d.project_id === Number(filters.project_id) : true) &&
        (filters.priority ? d.priority === filters.priority : true) &&
        (filters.q ? (d.title.toLowerCase().includes(filters.q.toLowerCase()) || (d.description||'').toLowerCase().includes(filters.q.toLowerCase())) : true) &&
        (st==='all' ? true : d.status===st)
    );
  }, [defects, tab, filters]);

  const statusCounts = useMemo(() => {
    const c = { all: defects.length, new:0,in_progress:0,review:0,closed:0,cancelled:0 };
    defects.forEach(d => { c[d.status] = (c[d.status]||0)+1; });
    return c;
  }, [defects]);

  const createDefect = async () => {
    try {
      if (!newDefect.project_id || !newDefect.title) return;
      let attachment_url = null;
      if (newDefect.file) {
        const fd = new FormData();
        fd.append('file', newDefect.file);
        const up = await api.post('/upload', fd, { headers: { 'Content-Type':'multipart/form-data' }});
        attachment_url = up.data.url;
      }
      await api.post('/defects', {
        project_id: Number(newDefect.project_id),
        title: newDefect.title,
        description: newDefect.description,
        priority: newDefect.priority,
        attachment_url
      });
      setDialogDefect(false);
      setNewDefect({ project_id:'', title:'', description:'', priority:'medium', file:null });
      setToast({ open:true, msg:'Дефект создан', severity:'success' });
      load();
    } catch {
      setToast({ open:true, msg:'Ошибка', severity:'error' });
    }
  };

  const createProject = async () => {
    try {
      if (!newProject.name.trim()) return;
      await api.post('/projects', newProject);
      setDialogProject(false);
      setNewProject({ name:'', description:'' });
      setToast({ open:true, msg:'Проект создан', severity:'success' });
      load();
    } catch {
      setToast({ open:true, msg:'Нет прав (manager only)', severity:'error' });
    }
  };

  return (
      <AppLayout
          title="Defect Tracker Lite"
          subtitle="Мини-реестр дефектов"
          actions={
            <Box sx={{ display:'flex', gap:1 }}>
              {role==='manager' && <Button variant="outlined" onClick={()=>setDialogProject(true)}>Новый проект</Button>}
              <Button variant="contained" onClick={()=>setDialogDefect(true)}>Новый дефект</Button>
            </Box>
          }
      >
        <Paper sx={{ p: 2, mb:2 }}>
          <Box sx={{ display:'flex', alignItems:'center', gap:2, flexWrap:'wrap' }}>
            <TextField select label="Проект" value={filters.project_id} onChange={e=>setFilters({...filters, project_id:e.target.value})} sx={{ minWidth:220 }}>
              <MenuItem value="">Все</MenuItem>
              {projects.map(p => <MenuItem key={p.id} value={String(p.id)}>{p.name}</MenuItem>)}
            </TextField>
            <TextField select label="Приоритет" value={filters.priority} onChange={e=>setFilters({...filters, priority:e.target.value})} sx={{ minWidth:180 }}>
              <MenuItem value="">Любой</MenuItem>
              <MenuItem value="low">low</MenuItem>
              <MenuItem value="medium">medium</MenuItem>
              <MenuItem value="high">high</MenuItem>
            </TextField>
            <TextField label="Поиск" value={filters.q} onChange={e=>setFilters({...filters, q:e.target.value})} sx={{ minWidth:240 }} />
            <Tabs value={tab} onChange={(_,v)=>setTab(v)} variant="scrollable" scrollButtons="auto" sx={{ ml:1 }}>
              {STATUS.map((s) => (
                  <Tab key={s} label={`${STATUS_LABEL[s]} (${statusCounts[s]||0})`} />
              ))}
            </Tabs>
          </Box>
        </Paper>

        {loading ? (
            <Box sx={{ display:'grid', placeItems:'center', height:200 }}><CircularProgress /></Box>
        ) : (
            <Grid container spacing={2}>
              {filtered.map(d => (
                  <Grid item xs={12} md={6} lg={4} key={d.id}>
                    <Paper sx={{ p:2, height:'100%' }}>
                      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{d.title}</Typography>
                        <Chip size="small" color={PRIORITY_COLOR[d.priority] || 'default'} label={d.priority} />
                      </Box>
                      <Typography variant="body2" color="text.secondary">{d.project_name}</Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>{d.description || '—'}</Typography>
                      {d.attachment_url && (
                          <Box sx={{ mt: 1 }}>
                            <Link href={d.attachment_url} target="_blank" rel="noreferrer" sx={{ display:'inline-flex', alignItems:'center', gap:0.5 }}>
                              <AttachmentIcon fontSize="small" /> вложение
                            </Link>
                          </Box>
                      )}
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                        <Chip size="small" variant="outlined" color={STATUS_COLOR[d.status] || 'default'} label={STATUS_LABEL[d.status]||d.status} />
                        <Typography variant="caption" color="text.secondary">{new Date(d.created_at).toLocaleString()}</Typography>
                      </Box>
                    </Paper>
                  </Grid>
              ))}
              {!filtered.length && (
                  <Grid item xs={12}>
                    <Paper sx={{ p:4, textAlign:'center' }}>
                      <Typography>Ничего не найдено</Typography>
                    </Paper>
                  </Grid>
              )}
            </Grid>
        )}

        {/* Dialog: New Defect */}
        <Dialog open={dialogDefect} onClose={()=>setDialogDefect(false)} fullWidth maxWidth="sm">
          <DialogTitle>Новый дефект</DialogTitle>
          <DialogContent sx={{ pt: 2, display:'flex', flexDirection:'column', gap:2 }}>
            <TextField select label="Проект" value={newDefect.project_id} onChange={e=>setNewDefect({...newDefect, project_id:Number(e.target.value)})}>
              {projects.map(p => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
            </TextField>
            <TextField label="Заголовок" value={newDefect.title} onChange={e=>setNewDefect({...newDefect, title:e.target.value})} />
            <TextField label="Описание" multiline minRows={3} value={newDefect.description} onChange={e=>setNewDefect({...newDefect, description:e.target.value})} />
            <TextField select label="Приоритет" value={newDefect.priority} onChange={e=>setNewDefect({...newDefect, priority:e.target.value})}>
              <MenuItem value="low">low</MenuItem>
              <MenuItem value="medium">medium</MenuItem>
              <MenuItem value="high">high</MenuItem>
            </TextField>
            <Button component="label" variant="outlined">
              Прикрепить файл (png/jpg/webp/pdf)
              <input type="file" accept=".png,.jpg,.jpeg,.webp,.pdf" hidden onChange={(e)=>setNewDefect({...newDefect, file:e.target.files?.[0] || null})} />
            </Button>
          </DialogContent>
          <DialogActions>
            <Button onClick={()=>setDialogDefect(false)}>Отмена</Button>
            <Button variant="contained" onClick={createDefect}>Создать</Button>
          </DialogActions>
        </Dialog>

        {/* Dialog: New Project */}
        <Dialog open={dialogProject} onClose={()=>setDialogProject(false)} fullWidth maxWidth="sm">
          <DialogTitle>Новый проект</DialogTitle>
          <DialogContent sx={{ pt: 2, display:'flex', flexDirection:'column', gap:2 }}>
            <TextField label="Название" value={newProject.name} onChange={e=>setNewProject({...newProject, name:e.target.value})} />
            <TextField label="Описание" multiline minRows={3} value={newProject.description} onChange={e=>setNewProject({...newProject, description:e.target.value})} />
          </DialogContent>
          <DialogActions>
            <Button onClick={()=>setDialogProject(false)}>Отмена</Button>
            <Button variant="contained" onClick={createProject}>Создать</Button>
          </DialogActions>
        </Dialog>

        <Toaster open={toast.open} message={toast.msg} severity={toast.severity} onClose={()=>setToast({...toast, open:false})} />
      </AppLayout>
  );
}

export default function App() {
  const [ready, setReady] = useState(!!localStorage.getItem('token'));
  return (
      <ThemeProvider theme={theme}>
        {ready ? <Dashboard /> : <Login onLogged={()=>setReady(true)} />}
      </ThemeProvider>
  );
}
