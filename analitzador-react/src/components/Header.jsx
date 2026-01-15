import './Header.css';

/**
 * Componente Header - Cabecera principal de la aplicación
 * Port del header de visualizador.html
 */
export function Header({
    title = "📊 Visualizador de Datos - Análisis de Noticias",
    subtitle = "Herramienta interactiva para analizar noticias clasificadas sobre China"
}) {
    return (
        <header className="header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </header>
    );
}

export default Header;
