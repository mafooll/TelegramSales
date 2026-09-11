catalog-hub = Управление каталогом
catalog-hub-catalogs-button = 🗂 Каталоги
catalog-hub-brands-button = 🏷 Бренды

catalog-list =
    { $total ->
        [one] { $total } каталог
        [few] { $total } каталога
       *[other] { $total } каталогов
    }
catalog-list-empty = Каталогов пока нет.
catalog-item = { $title } · { $count }
catalog-item-hidden = 🚫 { $title } · { $count }
catalog-card =
    Каталог: { $title }
    { $count ->
        [0] { "Категорий нет" }
        [one] { $count } категория
        [few] { $count } категории
       *[other] { $count } категорий
    }
catalog-create-button = ➕ Новый каталог
catalog-ask-title = Пришлите название каталога.
catalog-ask-new-title = Пришлите новое название каталога.

catalog-category-item = { $title } · { $count }
catalog-category-item-hidden = 🚫 { $title } · { $count }
catalog-category-card =
    Категория: { $title }
    { $count ->
        [0] { "Подкатегорий нет" }
        [one] { $count } подкатегория
        [few] { $count } подкатегории
       *[other] { $count } подкатегорий
    }
catalog-category-create-button = ➕ Новая категория
catalog-subcategory-create-button = ➕ Новая подкатегория
catalog-category-ask-title = Пришлите название категории.
catalog-category-ask-new-title = Пришлите новое название категории.

catalog-brand-list =
    { $total ->
        [one] { $total } бренд
        [few] { $total } бренда
       *[other] { $total } брендов
    }
catalog-brand-list-empty = Брендов пока нет.
catalog-brand-item = { $title }
catalog-brand-item-hidden = 🚫 { $title }
catalog-brand-card = Бренд: { $title }
catalog-brand-create-button = ➕ Новый бренд
catalog-brand-ask-title = Пришлите название бренда.
catalog-brand-ask-new-title = Пришлите новое название бренда.

catalog-rename-button = ✏️ Переименовать
catalog-hide-button = 🚫 Скрыть
catalog-show-button = ♻️ Вернуть
catalog-delete-button = 🗑 Удалить
catalog-back-button = ⬅️ Назад
catalog-cancel-button = Отмена

catalog-deleted = Удалено.
catalog-cancelled = Отменено.
catalog-delete-question = Удалить «{ $title }»?
catalog-title-rejected = Название не подходит: до 48 символов и не пустое.
catalog-title-taken = Такое название уже есть.
