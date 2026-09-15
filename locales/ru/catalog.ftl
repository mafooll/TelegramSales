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
catalog-delete-button = 🗑️ Удалить
catalog-back-button = ⬅️ Назад
catalog-cancel-button = Отмена

catalog-deleted = Удалено.
catalog-delete-question = Удалить «{ $title }»?
catalog-title-rejected = Название не подходит: до 48 символов и не пустое.
catalog-title-taken = Такое название уже есть.

catalog-product-list =
    { $total ->
        [one] { $total } товар
        [few] { $total } товара
       *[other] { $total } товаров
    }
catalog-product-list-empty = Товаров в этой категории пока нет.
catalog-product-item = { $title } · { $price }
catalog-product-item-draft = ✏️ { $title } · { $price }
catalog-product-item-hidden = 🚫 { $title } · { $price }

catalog-product-card =
    { $title }
    Артикул: { $article }
    Цена: { $price }

    { $description }

    Фото: { $photos } · Видео: { $videos } · Варианты: { $variants }
catalog-product-card-sale =
    { $title }
    Артикул: { $article }
    Цена: { $price } (было { $old_price })

    { $description }

    Фото: { $photos } · Видео: { $videos } · Варианты: { $variants }

catalog-open-products-button = 📦 Товары
catalog-open-catalog-products-button = 📦 Товары каталога ({ $count })
catalog-new-product-button = ➕ Новый товар
catalog-product-name-button = ✏️ Название
catalog-product-description-button = 📝 Описание
catalog-product-price-button = 💰 Цена
catalog-product-publish-button = ✅ Опубликовать
catalog-product-stock-button = 📦 В наличии
catalog-product-out-button = 📭 Нет в наличии
catalog-product-media-button = 🖼 Фото и видео
catalog-product-variants-button = 📐 Варианты

catalog-product-ask-title = Пришлите название товара.
catalog-product-ask-description = Пришлите описание товара.
catalog-product-ask-price = Пришлите цену — только число, например 12900.
catalog-product-ask-new-title = Пришлите новое название товара.
catalog-product-ask-new-description = Пришлите новое описание товара.
catalog-product-ask-new-price = Пришлите новую цену.
catalog-product-price-rejected = Цена не распознана. Пришлите число, например 12900.

catalog-media-screen =
    { $title }
    Фото: { $photos } из 10 · Видео: { $videos } из 1

    Пришлите снимки — можно альбомом. Нажмите на файл в списке, чтобы удалить.
catalog-media-item = 🖼 Удалить фото
catalog-media-video-item = 🎬 Удалить видео
catalog-ask-photo = Пришлите фотографии — можно альбомом.
catalog-ask-video = Пришлите видеообзор.
catalog-add-photo-button = ➕ Фото
catalog-add-video-button = ➕ Видео
catalog-done-button = ✅ Готово

catalog-variant-screen =
    { $title }
    Ось: { $label } · вариантов: { $total }

    Нажмите на вариант, чтобы переключить наличие.
catalog-variant-screen-closed =
    { $title }
    Варианты не заданы. Назовите ось — например «Размер» или «Объём».
catalog-variant-item = { $title } · { $price }
catalog-variant-item-out = 🚫 { $title } · { $price }
catalog-ask-axis = Как называется ось вариантов? Например «Размер».
catalog-ask-variant = Пришлите название варианта — например «M».
catalog-axis-button = 📐 Ось вариантов
catalog-add-variant-button = ➕ Вариант
catalog-media-rejected =
    Это не фото и не видео. Пришлите снимок или видеофайл — кружок и голосовое не подойдут.
catalog-media-as-file =
    Видео пришло файлом — Telegram такой файл в карточку не пустит.
    Отправьте его как видео: в меню вложения выберите «Видео», а не «Файл».
catalog-layout-collage-button = 🔲 Коллажем
catalog-layout-slideshow-button = 🎞 Каруселью
catalog-product-brand-button = 🏷 Бренд
catalog-brand-picker =
    { $title }
    Бренд: { $brand }
catalog-brand-unknown = не указан
catalog-brand-entry = { $title }
catalog-product-new-brand-button = ➕ Новый бренд
catalog-open-catalog-products-empty-button = 📦 Товары каталога

catalog-variant-card =
    { $product }
    { $label }: { $title }
    Цена: { $price }
catalog-variant-rename-button = ✏️ Название
catalog-variant-price-button = 💲 Цена
catalog-variant-drop-button = 🗑️ Удалить
catalog-variant-on-button = ✅ В наличии
catalog-variant-off-button = 🚫 Нет в наличии
catalog-variant-drop-question = Удалить вариант { $title }?
catalog-variant-ask-title = Пришлите новое название варианта.
catalog-variant-ask-price = Пришлите новую цену варианта.
catalog-back-to-variants-button = ⬅️ К вариантам

catalog-product-move-button = 📂 Перенести
catalog-product-move-catalog-picker =
    { $title }

    Куда переносим? Выберите каталог.
catalog-product-move-category-picker =
    { $title }

    Каталог: { $catalog }. Выберите категорию.
catalog-product-move-catalog-entry = { $title }
catalog-product-move-category-entry = { $title }
catalog-product-move-into-catalog-button = 📦 Прямо в каталог
catalog-product-moved = Товар перенесён.

catalog-error-needs-photo = Нельзя опубликовать без фотографии. Добавьте хотя бы одну.
catalog-error-needs-brand = Нельзя опубликовать без бренда. Выберите бренд.
catalog-error-too-many-photos = Больше фотографий добавить нельзя.
catalog-error-too-many-videos = Видео может быть только одно.
catalog-error-variants-not-allowed = У товара не задана ось вариантов.
catalog-error-price-not-positive = Цена должна быть больше нуля.
catalog-error-price-not-discounted = Старая цена должна быть выше новой.
catalog-error-description-empty = Описание не может быть пустым.
catalog-error-description-too-long = Описание слишком длинное.
catalog-error-title-empty = Название не может быть пустым.
catalog-error-title-too-long = Название слишком длинное.
catalog-error-nesting-too-deep = Глубже двух уровней категории не вкладываются.
catalog-error-foreign-catalog = Категория из другого каталога.
catalog-error-catalog-not-empty = В каталоге есть категории — сначала удалите их.
catalog-error-catalog-holds-products = В каталоге есть товары — сначала удалите их.
catalog-error-catalog-holds-categories = Каталог разделён на категории — товар без категории в него не положить.
catalog-error-category-not-empty = В категории есть подкатегории — сначала удалите их.
catalog-error-category-holds-products = В категории есть товары — сначала удалите или перенесите их.
catalog-error-brand-in-use = Бренд стоит у товаров — сначала смените его у них.
catalog-product-ask-brand-title = Пришлите название нового бренда — он сразу встанет товару.
