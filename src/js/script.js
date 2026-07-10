// ── 1. 상태 관리 및 전역 변수 ──
let favorites = JSON.parse(localStorage.getItem("jogiyo_favs")) || [];
let currentResults = [];
let currentModalImages = [];
let currentModalIndex = 0;

// ── 2. DOM 요소 ──
const restaurantList = document.getElementById("restaurantList");
const favList = document.getElementById("favList");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const themeToggle = document.getElementById("themeToggle");
const imageModal = document.getElementById("imageModal");
const fullImage = document.getElementById("fullImage");
const filterBar = document.getElementById("filterBar");

// ── 3. 초기 설정 (테마 및 빈 화면) ──
const currentTheme = localStorage.getItem("jogiyo_theme");
if (currentTheme === "dark") {
	document.body.classList.add("dark-mode");
	themeToggle.textContent = "☀️";
}

const emptyCopies = ["오늘도 '아무거나'는 없습니다 🙅", "AI는 이미 맛집을 알고 있어요. 당신만 모를 뿐 🤫", "오늘 점심, 아직도 고민 중이세요? 🤔", "당신의 위장이 원하는 곳, AI가 찾아드려요 🤖", "검색 한 번으로 후회 없는 한 끼를 🍜", "맛집 고민에 쓰는 시간, 이제 AI한테 넘기세요 ⏱️"];

const showEmptyMessage = () => {
	const randomIndex = Math.floor(Math.random() * emptyCopies.length);
	const emptyMessage = document.getElementById("emptyMessage");
	emptyMessage.querySelector(".empty-copy").textContent = emptyCopies[randomIndex];
	emptyMessage.style.display = "flex";
};
const hideEmptyMessage = () => (document.getElementById("emptyMessage").style.display = "none");
showEmptyMessage(); // 접속 시 최초 실행

// ── 4. 메인 검색 및 API 로직 ──
const handleSearch = () => {
	if (searchBtn.disabled) return;
	const query = searchInput.value.trim();
	if (!query) {
		showToast("⚠️ 검색어를 입력해주세요!");
		searchInput.focus();
		return;
	}
	hideEmptyMessage();
	fetchRecommendations(query);
};

const fetchRecommendations = async (query) => {
	restaurantList.innerHTML = `
        <div class="loading-container empty-message" style="display:flex;">
            <div class="spinner">🍽️</div>
            <p class="empty-copy">AI가 진짜 맛집을 찾고 있어요<br><span class="sub-text">네이버 교차 검증 중... (최대 15초)</span></p>
        </div>
    `;
	filterBar.innerHTML = ""; // 검색 시작 시 기존 필터 초기화

	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 15000);

	try {
		const response = await fetch("/api/ai", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ query }),
			signal: controller.signal,
		});
		clearTimeout(timeoutId);

		if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

		const data = await response.json();

		// [핵심 수정] 받아온 데이터를 전역 변수에 반드시 저장해야 필터링이 동작합니다!
		currentResults = data;

		renderCards(currentResults, restaurantList);
		renderFilters(currentResults);
	} catch (error) {
		console.error("Error:", error);
		if (error.name === "AbortError") {
			restaurantList.innerHTML = '<div class="empty-msg empty-message">요청 시간이 초과되었습니다. 다시 시도해주세요 ⏳</div>';
		} else {
			restaurantList.innerHTML = '<div class="empty-msg empty-message">서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요 🚨</div>';
		}
	}
};

// ── 5. UI 렌더링 로직 (카드 및 필터) ──
const renderCards = (data, targetElement) => {
	if (!data || data.length === 0) {
		targetElement.innerHTML = '<div class="empty-msg empty-message">조건에 맞는 맛집 데이터를 찾지 못했습니다.</div>';
		return;
	}

	targetElement.innerHTML = data
		.map((store) => {
			const isFav = favorites.some((f) => f.id === store.id);
			const storeJson = JSON.stringify(store).replace(/'/g, "&#39;");
			const imagesArray = store.images || [];
			const firstImg = imagesArray.length > 0 ? imagesArray[0] : "https://via.placeholder.com/300?text=No+Image";
			const isNoImage = firstImg.includes("via.placeholder.com");

			const extraCount = isNoImage ? 0 : imagesArray.length - 1;
			const badgeHtml = extraCount > 0 ? `<div class="image-count-badge">+${extraCount}</div>` : "";
			const imagesJson = JSON.stringify(imagesArray).replace(/"/g, "&quot;");
			const addressText = store.address || store.location || "주소 정보 없음";

			const clickEvent = isNoImage ? "" : `onclick='openModal(${imagesJson}, 0)'`;
			const cursorStyle = isNoImage ? "cursor: default;" : "cursor: pointer;";

			return `
        <div class="card">
            <button class="fav-btn ${isFav ? "active" : ""}" onclick='toggleFavorite(${storeJson}, this)'>
                <svg viewBox="0 0 24 24" class="heart-icon"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </button>
            <button class="map-btn" onclick="openMap('${addressText}', '${store.name}')">🗺️</button>
            
            <div class="image-container" ${clickEvent} style="${cursorStyle}">
                <img src="${firstImg}" class="card-img" alt="가게 이미지">
                ${badgeHtml}
            </div>
            
            <div class="card-info">
                <div class="card-header">
                    <h4>${store.name}</h4>
                    <span class="category-badge">${store.category || "맛집"}</span>
                </div>
                <p class="desc">${store.desc}</p>
                <div class="card-footer">
                    <div class="address-wrapper">
                        <p class="address" style="cursor:pointer; text-decoration:underline;text-align-last:center" onclick="copyAddress('${addressText}')">
                            📍 ${addressText}
                        </p>
                    </div>
                    <div class="action-buttons">
                        <a href="${store.link}" target="_blank" class="link-btn">네이버 검색 ➔</a>
                        <button class="share-btn" onclick='shareStore(${storeJson})'>공유</button>
                    </div>
                </div>
            </div>
        </div>`;
		})
		.join("");
};

const renderFilters = (data) => {
	if (!data || data.length === 0) return;
	const categories = ["전체", ...new Set(data.map((item) => (item.category || "기타").trim()))];
	filterBar.innerHTML = categories.map((cat) => `<button onclick="filterResults('${cat}')">${cat}</button>`).join("");
};

window.filterResults = (category) => {
	if (category === "전체") {
		renderCards(currentResults, restaurantList);
		return;
	}
	const filtered = currentResults.filter((item) => {
		return (item.category || "기타").trim() === category.trim();
	});
	renderCards(filtered, restaurantList);
};

// ── 6. 부가 기능 (즐겨찾기, 복사, 공유, 토스트) ──
window.toggleFavorite = (store, btnElement) => {
	const index = favorites.findIndex((f) => f.id === store.id);
	const isAdding = index === -1;

	if (isAdding) {
		favorites.push(store);
		btnElement.classList.add("active");
	} else {
		favorites.splice(index, 1);
		btnElement.classList.remove("active");
	}
	localStorage.setItem("jogiyo_favs", JSON.stringify(favorites));

	if (document.getElementById("favPage").style.display === "block") {
		renderCards(favorites, favList);
	}
	showToast(isAdding ? "❤️ 즐겨찾기에 추가되었습니다!" : "🤍 즐겨찾기에서 삭제되었습니다.");
};

window.copyAddress = (address) => {
	navigator.clipboard
		.writeText(address)
		.then(() => showToast("📍 주소가 복사되었습니다."))
		.catch(() => showToast("❌ 복사 실패"));
};

window.shareStore = (store) => {
	if (navigator.share) {
		navigator.share({ title: "저기요.ai 추천 맛집", text: `${store.name} 어때? ${store.desc}`, url: store.link }).catch(console.error);
	} else {
		copyAddress(store.link);
		showToast("링크가 복사되었습니다!");
	}
};

const showToast = (msg) => {
	let container = document.getElementById("toastContainer");
	if (!container) {
		container = document.createElement("div");
		container.id = "toastContainer";
		container.className = "toast-container";
		document.body.appendChild(container);
	}
	const toast = document.createElement("div");
	toast.className = "toast";
	toast.textContent = msg;
	container.appendChild(toast);
	setTimeout(() => toast.classList.add("show"), 10);
	setTimeout(() => {
		toast.classList.remove("show");
		setTimeout(() => toast.remove(), 300);
	}, 2500);
};

// ── 7. 모달 로직 (이미지 및 지도) ──
window.openModal = (images, index = 0) => {
	currentModalImages = images;
	currentModalIndex = index;
	updateModalImage();
	imageModal.style.display = "flex";
};

window.updateModalImage = () => {
	fullImage.src = currentModalImages[currentModalIndex];
	const showNav = currentModalImages.length > 1 ? "block" : "none";
	document.getElementById("prevBtn").style.display = showNav;
	document.getElementById("nextBtn").style.display = showNav;
	document.getElementById("modalCounter").style.display = showNav;
	document.getElementById("modalCounter").innerText = `${currentModalIndex + 1} / ${currentModalImages.length}`;
};

window.changeModalImage = (step) => {
	currentModalIndex += step;
	if (currentModalIndex < 0) currentModalIndex = currentModalImages.length - 1;
	if (currentModalIndex >= currentModalImages.length) currentModalIndex = 0;
	updateModalImage();
};

window.closeModal = () => (imageModal.style.display = "none");

window.openMap = (address, name) => {
	const mapUrl = `https://map.naver.com/v5/search/${encodeURIComponent(address)} ${encodeURIComponent(name)}`;
	document.getElementById("mapFrame").src = mapUrl;
	document.getElementById("mapModal").style.display = "flex";
};

window.closeMapModal = () => (document.getElementById("mapModal").style.display = "none");

// ── 8. 이벤트 리스너 등록 ──
searchBtn.addEventListener("click", handleSearch);
searchInput.addEventListener("keydown", (e) => {
	if (e.key === "Enter") {
		e.preventDefault();
		handleSearch();
	}
});

themeToggle.addEventListener("click", () => {
	document.body.classList.toggle("dark-mode");
	const isDark = document.body.classList.contains("dark-mode");
	themeToggle.textContent = isDark ? "☀️" : "🌙";
	localStorage.setItem("jogiyo_theme", isDark ? "dark" : "light");
});

const showPage = (page) => {
	const isHome = page === "home";
	document.getElementById("homePage").style.display = isHome ? "block" : "none";
	document.getElementById("favPage").style.display = isHome ? "none" : "block";
	document.getElementById("menuHome").classList.toggle("active", isHome);
	document.getElementById("menuFav").classList.toggle("active", !isHome);
	if (!isHome) renderCards(favorites, favList);
};

document.getElementById("menuHome").onclick = () => showPage("home");
document.getElementById("menuFav").onclick = () => showPage("fav");
document.getElementById("goHome").onclick = () => showPage("home");

// 모달 바깥 영역 클릭 시 닫기
window.addEventListener("click", (e) => {
	if (e.target === imageModal) closeModal();
	if (e.target.id === "mapModal") closeMapModal();
});
