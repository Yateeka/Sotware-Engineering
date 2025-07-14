import { Box } from '@mui/material';
import { AppProps } from 'next/app';
import Head from 'next/head';
import Navigation from '../components/global/Navigation';
import '../global.css';

const App = ({ Component, pageProps }: AppProps) => {
    return (
        <>
            <Head>
                <title>Global Protest Tracker</title>
                <meta name="viewport" content="initial-scale=1.0, width=device-width" />
            </Head>

            <Box display="flex" minHeight="100vh">
                <Navigation />
                <Box flexGrow={1} ml="64px" width="100%">
                    <Component {...pageProps} />
                </Box>
            </Box>
        </>
    );
};

export default App;
