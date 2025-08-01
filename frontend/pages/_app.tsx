import { Box } from '@mui/material';
import { AppProps } from 'next/app';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Navigation from '../components/global/Navigation';
import '../global.css';

const App = ({ Component, pageProps }: AppProps) => {
    const router = useRouter();
    
    // Determine if we should show navigation
    // Hide navigation on specific pages if needed
    const hideNavigation = ['/login', '/register'].includes(router.pathname);
    
    // Determine margin based on navigation visibility
    const mainMargin = hideNavigation ? '0' : '64px';

    return (
        <>
            <Head>
                <title>Global Protest Tracker</title>
                <meta name="viewport" content="initial-scale=1.0, width=device-width" />
                <meta name="description" content="Track protests, social movements, and civic actions happening around the world. Stay informed about demonstrations for human rights, climate action, and social justice." />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <Box display="flex" minHeight="100vh">
                {!hideNavigation && <Navigation />}
                
                <Box 
                    flexGrow={1} 
                    ml={mainMargin} 
                    width="100%"
                    sx={{
                        transition: 'margin-left 0.3s ease-in-out',
                        // Ensure content doesn't go under navigation on mobile
                        '@media (max-width: 768px)': {
                            ml: hideNavigation ? '0' : '64px'
                        }
                    }}
                >
                    <Component {...pageProps} />
                </Box>
            </Box>
        </>
    );
};

export default App;