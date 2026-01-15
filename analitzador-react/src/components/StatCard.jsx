import './StatCard.css';

/**
 * Componente StatCard - Tarjeta de estadísticas
 * Port de las stat-card de visualizador.html
 * 
 * @param {string} icon - Emoji o icono a mostrar
 * @param {string|number} value - Valor numérico de la estadística
 * @param {string} label - Etiqueta descriptiva
 * @param {string} trend - Opcional: 'up', 'down', 'neutral' para mostrar tendencia
 */
export function StatCard({
    icon,
    value,
    label,
    trend = null,
    loading = false
}) {
    const getTrendClass = () => {
        if (!trend) return '';
        return `stat-card--${trend}`;
    };

    return (
        <div className={`stat-card ${getTrendClass()}`}>
            <div className="stat-card__icon">{icon}</div>
            <div className="stat-card__value">
                {loading ? (
                    <span className="stat-card__loading">...</span>
                ) : (
                    value
                )}
            </div>
            <div className="stat-card__label">{label}</div>
            {trend && (
                <div className={`stat-card__trend stat-card__trend--${trend}`}>
                    {trend === 'up' && '↑'}
                    {trend === 'down' && '↓'}
                    {trend === 'neutral' && '→'}
                </div>
            )}
        </div>
    );
}

export default StatCard;
