import { useState } from 'react';
import Header from './components/Header';
import StatCard from './components/StatCard';
import './App.css';

/**
 * App principal - Visualizador de Noticias de China
 * Port progresivo desde visualizador.html
 */
function App() {
  // Estado de ejemplo con datos mock
  const [stats, setStats] = useState({
    totalNoticias: 1234,
    totalTemas: 15,
    totalMedios: 28,
    clasificadas: 987
  });

  return (
    <div className="container">
      {/* Header */}
      <Header
        title="📊 Visualizador de Datos - Análisis de Noticias"
        subtitle="Herramienta interactiva para analizar noticias clasificadas sobre China"
      />

      {/* Estadísticas */}
      <div className="stats-grid">
        <StatCard
          icon="📰"
          value={stats.totalNoticias}
          label="Total Noticias"
        />
        <StatCard
          icon="🏷️"
          value={stats.totalTemas}
          label="Temas Únicos"
        />
        <StatCard
          icon="📡"
          value={stats.totalMedios}
          label="Medios"
        />
        <StatCard
          icon="✅"
          value={stats.clasificadas}
          label="Clasificadas"
        />
      </div>

      {/* Placeholder para los componentes que faltan */}
      <div className="card" style={{ marginBottom: '30px' }}>
        <h2>🔍 Filtros</h2>
        <p style={{ color: 'var(--text-light)', marginTop: '10px' }}>
          Componente de filtros pendiente de portear...
        </p>
      </div>

      <div className="charts-grid">
        <div className="card">
          <h3>📊 Distribución por Tema</h3>
          <p style={{ color: 'var(--text-light)', marginTop: '10px' }}>
            Gráfico pendiente de portear...
          </p>
        </div>
        <div className="card">
          <h3>🖼️ Imagen de China</h3>
          <p style={{ color: 'var(--text-light)', marginTop: '10px' }}>
            Gráfico pendiente de portear...
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
