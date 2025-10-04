import { createTheme } from '@mui/material/styles';

const createAppTheme = (mode = 'light') =>
    createTheme({
      palette: {
        mode,
        primary: { main: '#635bff' },
        secondary: { main: '#7c69ef' },
      },
      shape: { borderRadius: 12 },
      typography: {
        fontFamily: `"Inter","system-ui","-apple-system","Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif`,
        h5: { fontWeight: 700 },
        subtitle1: { fontWeight: 700 },
      },
      components: {
        MuiInputLabel: { defaultProps: { shrink: true } },
        MuiPaper: {
          styleOverrides: {
            root: { backgroundImage: 'none', borderRadius: 12 },
            elevation1: {
              boxShadow: '0 2px 8px rgba(15,23,42,.08), 0 8px 24px rgba(15,23,42,.06)',
            },
          },
          defaultProps: { elevation: 1 },
        },
        MuiChip: {
          styleOverrides: { root: { fontWeight: 600 }, outlined: { borderColor: 'rgba(99,91,255,.35)' } },
          defaultProps: { size: 'small' },
        },
        MuiButton: { defaultProps: { size: 'small' }, styleOverrides: { root: { textTransform: 'none', fontWeight: 700 } } },
        MuiTextField: { defaultProps: { size: 'small', margin: 'dense' } },
        MuiTabs: { styleOverrides: { root: { minHeight: 36 }, indicator: { height: 2 } } },
        MuiTab: { styleOverrides: { root: { minHeight: 36 } } },
        MuiDialog: {
          defaultProps: {
            fullWidth: true,
            maxWidth: 'sm',
            BackdropProps: { sx: { backgroundColor: 'rgba(10, 12, 20, .45)', backdropFilter: 'blur(3px)' } },
          },
          styleOverrides: { paper: { padding: 8, borderRadius: 16, boxShadow: '0 18px 60px rgba(0,0,0,.35)' } },
        },
      },
    });

export default createAppTheme;
