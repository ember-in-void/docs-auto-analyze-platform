// ==========================================
// Badge — Status and type indicator
// ==========================================

const STATUS_CLASS = {
  active:    'badge-active',
  archived:  'badge-archived',
  completed: 'badge-completed',
}

const DOC_TYPE_CLASS = {
  TZ:           'badge-tz',
  ARCHITECTURE: 'badge-arch',
  REQUIREMENTS: 'badge-req',
  LOGS:         'badge-logs',
  OTHER:        'badge-other',
}

const DOC_TYPE_LABEL = {
  TZ:           'Тех. задание',
  ARCHITECTURE: 'Архитектура',
  REQUIREMENTS: 'Требования',
  LOGS:         'Логи',
  OTHER:        'Прочее',
}

const STATUS_LABEL = {
  active:    'Активный',
  archived:  'Архив',
  completed: 'Завершён',
}

export function StatusBadge({ status }) {
  return (
    <span className={`badge ${STATUS_CLASS[status] ?? 'badge-other'}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  )
}

export function DocTypeBadge({ type }) {
  return (
    <span className={`badge ${DOC_TYPE_CLASS[type] ?? 'badge-other'}`}>
      {DOC_TYPE_LABEL[type] ?? type}
    </span>
  )
}
