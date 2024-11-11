import { renderVoyager } from 'graphql-voyager/dist/voyager.standalone'
import 'graphql-voyager/dist/voyager.css';

renderVoyager(document.getElementById('voyager'), {
    introspection: null,
    allowToChangeSchema: true,
    hideVoyagerLogo: false,
});
