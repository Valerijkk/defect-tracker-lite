import React, { useEffect, useMemo, useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import createAppTheme from './theme';
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
import Link from '@mui/material/Link';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import MenuItem from '@mui/material/MenuItem';
import CircularProgress from '@mui/material/CircularProgress';
import AttachmentIcon from '@mui/icons-material/AttachFile';
import OutlinedInput from '@mui/material/OutlinedInput';


import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';

const STATUS = ['all','new','in_progress','review','closed','cancelled'];
const STATUS_LABEL = {
  all:'Все',
  new:'New',
  in_progress:'In progress',
  review:'Review',
  closed:'Closed',
  cancelled:'Cancelled'
};
const STATUS_COLOR = {
  new:'info',
  in_progress:'warning',
  review:'secondary',
  closed:'success',
  cancelled:'default'
};
const PRIORITY_COLOR = { low:'default', medium:'primary', high:'error' };

function detectInitialMode() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light' || saved === 'dark') return saved;
  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

function Login({ onLogged }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState(isRegister ? '' : 'admin@example.com');
  const [password, setPassword] = useState(isRegister ? '' : 'admin123');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // гарантируем, что админ появится на чистой БД
  React.useEffect(() => { api.post('/setup/bootstrap').catch(()=>{}); }, []);

  const finishAuth = async (token, role, emailFromApi) => {
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    if (emailFromApi) localStorage.setItem('email', emailFromApi);
    api.defaults.headers.common.Authorization = 'Bearer ' + token; // сразу ставим хедер
    await api.get('/health').catch(()=>{});
    onLogged();
  };

  const submit = async () => {
    try {
      setLoading(true); setError('');
      if (isRegister) {
        if (!email || !password) throw new Error('Введите email и пароль');
        if (password !== password2) throw new Error('Пароли не совпадают');
        const { data } = await api.post('/auth/register', { email, password });
        await finishAuth(data.token, data.role, data.email);
      } else {
        const { data } = await api.post('/auth/login', { email, password });
        await finishAuth(data.token, data.role, data.email);
      }
    } catch (e) {
      const msg = e?.response?.data?.error || e.message || 'Ошибка авторизации';
      setError(msg);
    } finally { setLoading(false); }
  };

  return (
      <Box sx={{ display:'grid', placeItems:'center', minHeight:'70vh' }}>
        <Paper sx={{ p: 4, width: 420 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {isRegister ? 'Регистрация' : 'Вход'}
          </Typography>
          {!isRegister && (
              <Typography variant="body2" color="text.secondary">
                demo: admin@example.com / admin123
              </Typography>
          )}
          <TextField label="Email" fullWidth sx={{ mt: 2 }} value={email} onChange={e=>setEmail(e.target.value)} />
          <TextField label="Пароль" fullWidth sx={{ mt: 2 }} type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {isRegister && (
              <TextField label="Повторите пароль" fullWidth sx={{ mt: 2 }} type="password" value={password2} onChange={e=>setPassword2(e.target.value)} />
          )}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{String(error)}</Alert>}
          <Button disabled={loading} variant="contained" sx={{ mt: 2 }} onClick={submit}>
            {isRegister ? 'Создать аккаунт' : 'Войти'}
          </Button>
          <Button sx={{ mt: 1 }} onClick={()=>{ setIsRegister(!isRegister); setError(''); }}>
            {isRegister ? 'Есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}
          </Button>
        </Paper>
      </Box>
  );
}

function Dashboard({ themeMode, onToggleTheme }) {
  const [dialogStatus, setDialogStatus] = useState(false);
  const [selectedDefect, setSelectedDefect] = useState(null);
  const [newStatus, setNewStatus] = useState('new');

  // Create project
  const [dialogProject, setDialogProject] = useState(false);
  const [newProject, setNewProject] = useState({ name:'', description:'' });

  // Create defect
  const [dialogDefect, setDialogDefect] = useState(false);
  const [newDefect, setNewDefect] = useState({ project_id:'', title:'', description:'', priority:'medium' });

  // Profile
  const [dialogProfile, setDialogProfile] = useState(false);

  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState(0);
  const [projects, setProjects] = useState([]);
  const [defects, setDefects] = useState([]);
  const [toast, setToast] = useState({ open:false, msg:'', severity:'success' });

  const userEmail = localStorage.getItem('email') || 'user@local';
  const userRole = localStorage.getItem('role') || 'engineer';

  const [filters, setFilters] = useState({ project_id:'', priority:'', q:'' });
  const STATUS_BY_INDEX = (i)=> STATUS[i] || 'all';

  useEffect(() => {
    const t = localStorage.getItem('token');
    if (t) api.defaults.headers.common.Authorization = 'Bearer ' + t;
  }, []);

  const load = async () => {
    try {
      setLoading(true);
      const [p, d] = await Promise.all([api.get('/projects'), api.get('/defects')]);
      setProjects(p.data); setDefects(d.data);
    } finally { setLoading(false); }
  };
  useEffect(()=>{ load(); }, []);

  const filtered = useMemo(() => {
    const st = STATUS_BY_INDEX(tab);
    return defects.filter(d =>
        (filters.project_id ? d.project_id === Number(filters.project_id) : true) &&
        (filters.priority ? d.priority === filters.priority : true) &&
        (filters.q ? (d.title.toLowerCase().includes(filters.q.toLowerCase()) || (d.description||'').toLowerCase().includes(filters.q.toLowerCase())) : true) &&
        (st === 'all' ? true : d.status === st)
    );
  }, [defects, filters, tab]);

  const statusCounts = useMemo(() => {
    const counts = { all: defects.length, new:0, in_progress:0, review:0, closed:0, cancelled:0 };
    defects.forEach(d => { counts[d.status] = (counts[d.status]||0)+1; });
    return counts;
  }, [defects]);

  const createProject = async () => {
    try {
      await api.post('/projects', newProject);
      setDialogProject(false); setNewProject({name:'', description:''});
      setToast({ open:true, msg:'Проект создан', severity:'success' });
      await load();
    } catch(e) {
      setToast({ open:true, msg:'Ошибка создания проекта', severity:'error' });
    }
  };

  const createDefect = async () => {
    try {
      if (!newDefect.project_id || !newDefect.title) return;
      await api.post('/defects', { ...newDefect, project_id: Number(newDefect.project_id) });
      setDialogDefect(false);
      setNewDefect({ project_id:'', title:'', description:'', priority:'medium' });
      setToast({ open:true, msg:'Дефект создан', severity:'success' });
      await load();
    } catch {
      setToast({ open:true, msg:'Ошибка создания дефекта', severity:'error' });
    }
  };

  return (
      <AppLayout
          userEmail={userEmail}
          onProfile={()=>setDialogProfile(true)}
          onLogout={() => {
            localStorage.removeItem('token'); localStorage.removeItem('role'); localStorage.removeItem('email');
            window.location.reload();
          }}
          themeMode={themeMode}
          onToggleTheme={onToggleTheme}
      >
        <Box sx={{ p: 2 }}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display:'flex', alignItems:'center', gap:1, flexWrap:'wrap' }}>
              <TextField
                  select
                  label="Проект"
                  value={filters.project_id}
                  onChange={e=>setFilters({...filters, project_id:e.target.value})}
                  sx={{ minWidth:180 }}
              >
                <MenuItem value="">Любой</MenuItem>
                {projects.map(p => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
              </TextField>

              <TextField
                  select
                  label="Приоритет"
                  value={filters.priority}
                  onChange={e=>setFilters({...filters, priority:e.target.value})}
                  sx={{ minWidth:180 }}
              >
                <MenuItem value="">Любой</MenuItem>
                <MenuItem value="low">low</MenuItem>
                <MenuItem value="medium">medium</MenuItem>
                <MenuItem value="high">high</MenuItem>
              </TextField>

              <TextField
                  label="Поиск"
                  value={filters.q}
                  onChange={e=>setFilters({...filters, q:e.target.value})}
                  sx={{ minWidth:240 }}
              />

              <Tabs value={tab} onChange={(_,v)=>setTab(v)} variant="scrollable" scrollButtons="auto" sx={{ ml:1 }}>
                {STATUS.map((s) => (
                    <Tab key={s} label={`${STATUS_LABEL[s]} (${statusCounts[s]||0})`} />
                ))}
              </Tabs>
            </Box>
          </Paper>

          {loading ? (
              <Box sx={{ display:'grid', placeItems:'center', height:200 }}>
                <CircularProgress />
              </Box>
          ) : (
              <Grid container spacing={2}>
                {filtered.map(d => (
                    <Grid item xs={12} md={6} lg={4} key={d.id}>
                      <Paper sx={{ p:2, height:'100%', border: '1px solid rgba(99,91,255,.12)' }}>
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

                        <Divider sx={{ my: 1.25 }} />

                        <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                          <Chip
                              size="small"
                              variant="outlined"
                              color={STATUS_COLOR[d.status] || 'default'}
                              label={STATUS_LABEL[d.status]||d.status}
                              onClick={()=>{ setSelectedDefect(d); setNewStatus(d.status); setDialogStatus(true); }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {new Date(d.created_at).toLocaleString()}
                          </Typography>
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

          <Box sx={{ mt: 2, display:'flex', gap:1 }}>
            <Button variant="outlined" onClick={()=>setDialogProject(true)}>Новый проект</Button>
            <Button variant="contained" onClick={()=>setDialogDefect(true)}>Новый дефект</Button>
          </Box>
        </Box>

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

        {/* Dialog: Change Status */}
        <Dialog
            open={dialogStatus}
            onClose={() => setDialogStatus(false)}
            fullWidth
            maxWidth="xs"
            PaperProps={{ sx: { overflow: 'visible' } }}
        >
          <DialogTitle>Изменить статус</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <TextField
                fullWidth
                size="small"
                select
                label="Статус"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                // критично: форсим shrink и фон под лейблом — в тёмной теме не режется
                InputLabelProps={{
                  shrink: true,
                  sx: (t) => ({ bgcolor: t.palette.background.paper, px: 0.5, zIndex: 1 }),
                }}
                SelectProps={{ MenuProps: { PaperProps: { sx: { maxHeight: 320, mt: 1 } } } }}
            >
              <MenuItem value="new">New</MenuItem>
              <MenuItem value="in_progress">In progress</MenuItem>
              <MenuItem value="review">Review</MenuItem>
              <MenuItem value="closed">Closed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogStatus(false)}>Отмена</Button>
            <Button
                variant="contained"
                onClick={async () => {
                  if (!selectedDefect) return;
                  await api.patch(`/defects/${selectedDefect.id}`, { status: newStatus });
                  setDefects((prev) =>
                      prev.map((x) => (x.id === selectedDefect.id ? { ...x, status: newStatus } : x))
                  );
                  setDialogStatus(false);
                }}
            >
              Сохранить
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog: Profile */}
        <Dialog open={dialogProfile} onClose={()=>setDialogProfile(false)} fullWidth maxWidth="xs">
          <DialogTitle>Профиль</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <Typography variant="body1"><b>Email:</b> {userEmail}</Typography>
            <Typography variant="body1"><b>Роль:</b> {userRole}</Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={()=>setDialogProfile(false)}>Закрыть</Button>
          </DialogActions>
        </Dialog>

        <Toaster open={toast.open} message={toast.msg} severity={toast.severity} onClose={()=>setToast({...toast, open:false})} />
      </AppLayout>
  );
}

export default function App() {
  const [mode, setMode] = useState(detectInitialMode());
  useEffect(() => { localStorage.setItem('theme', mode); }, [mode]);
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  const [ready, setReady] = useState(!!localStorage.getItem('token'));

  return (
      <ThemeProvider theme={theme}>
        {ready
            ? <Dashboard themeMode={mode} onToggleTheme={()=>setMode(m => (m === 'light' ? 'dark' : 'light'))} />
            : <Login onLogged={()=>setReady(true)} />}
      </ThemeProvider>
  );
}
