export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, retryAfter?: string | null) {
    const messages: Record<number, string> = {
      401: 'Сессия истекла или данные для входа неверны. Войдите снова.',
      403: 'Недостаточно прав для этого действия.',
      404: 'Объект не найден или больше недоступен.',
      409: 'Изменение невозможно: запись уже существует или это последний администратор.',
      422: 'Проверьте поля формы, исполнителя и теги. Данные могли измениться.',
      429: `Слишком много запросов. Повторите через ${retryAfter ?? 'несколько'} сек.`,
      503: 'Сервис временно недоступен. Повторите немного позже.',
    };
    super(messages[status] ?? 'Не удалось выполнить запрос. Повторите позже.');
    this.status = status;
  }
}
export function errorText(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Не удалось связаться с сервером. Проверьте подключение и повторите.';
}
