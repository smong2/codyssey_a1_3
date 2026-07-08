// 1. 상태 관리
let favorites = JSON.parse(localStorage.getItem("jogiyo_favs")) || [];

// 2. DOM 요소
const restaurantList = document.getElementById("restaurantList");
const favList = document.getElementById("favList");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

// 3. API 호출 함수
const fetchRecommendations = async (query) => {
	// [디자인 1] 중앙 정렬된 동글동글 로딩 애니메이션
	restaurantList.innerHTML = `
        <div class="loading-container empty-message" style="display:flex;">
            <div class="spinner">🍽️</div>
            <p class="empty-copy">AI가 맛집을 찾고 있어요<br><span class="sub-text">잠시만 기다려주세요...</span></p>
        </div>
    `;

	try {
		const response = await fetch("/api/ai", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ query }),
		});
		const data = await response.json();
		renderCards(data, restaurantList);
	} catch (error) {
		console.error("Error:", error);
		restaurantList.innerHTML = '<div class="empty-msg empty-message">오류가 발생했습니다. 다시 시도해주세요.</div>';
	}
};

// 4. 카드 렌더링 함수
const renderCards = (data, targetElement) => {
	if (!data || data.length === 0) {
		targetElement.innerHTML = '<div class="empty-msg empty-message">데이터가 없습니다.</div>';
		return;
	}

	targetElement.innerHTML = data
		.map((store) => {
			const isFav = favorites.some((f) => f.id === store.id);
            // JSON 변환 시 따옴표 충돌 방지
            const storeJson = JSON.stringify(store).replace(/'/g, "&#39;");
            
			return `
            <div class="card">
                <button class="fav-btn ${isFav ? "active" : ""}" onclick='toggleFavorite(${storeJson}, this)'>
                    <svg viewBox="0 0 24 24" class="heart-icon"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </button>
                
                <div class="slider-container multiple-images">
                    ${store.images.map((img) => `<img src="${img}" class="slider-img" onclick="openModal('${img}')">`).join("")}
                </div>
                
                <div class="card-info">
                    <div class="card-header">
                        <h4>${store.name}</h4>
                        <span class="category-badge">${store.category || '맛집'}</span>
                    </div>
                    <p class="desc">${store.desc}</p>
                    <div class="card-footer">
                        <p class="address">📍 ${store.address || store.location || '주소 정보 없음'}</p>
                        <a href="${store.link}" target="_blank" class="link-btn">네이버 검색 ➔</a>
                    </div>
                </div>
            </div>
        `;
		})
		.join("");
};

// 5. 즐겨찾기 토글 로직 [디자인 3, 4]
window.toggleFavorite = (store, btnElement) => {
	const index = favorites.findIndex((f) => f.id === store.id);
    const isAdding = index === -1;

	if (!isAdding) {
		favorites.splice(index, 1); // 해제
        btnElement.classList.remove("active"); // 클래스 즉시 제거
	} else {
		favorites.push(store); // 등록
        btnElement.classList.add("active"); // 클래스 즉시 추가
	}
	localStorage.setItem("jogiyo_favs", JSON.stringify(favorites));

	if (document.getElementById("favPage").style.display === "block") {
		renderCards(favorites, favList);
	}
	
    // alert 대신 토스트 팝업 호출
    showToast(isAdding ? "❤️ 즐겨찾기에 추가되었습니다!" : "🤍 즐겨찾기에서 삭제되었습니다.");
};

// [디자인 4] 토스트 팝업 함수 추가
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

// 6. 페이지 네비게이션
const showPage = (page) => {
	if (page === "home") {
		document.getElementById("homePage").style.display = "block";
		document.getElementById("favPage").style.display = "none";
		document.getElementById("menuHome").classList.add("active");
		document.getElementById("menuFav").classList.remove("active");
	} else {
		document.getElementById("homePage").style.display = "none";
		document.getElementById("favPage").style.display = "block";
		document.getElementById("menuHome").classList.remove("active");
		document.getElementById("menuFav").classList.add("active");
		renderCards(favorites, favList); // 즐겨찾기 목록 렌더링
	}
};

// 7. 이벤트 리스너 (기존 유지)
searchBtn.addEventListener("click", () => {
	hideEmptyMessage();
	const query = searchInput.value.trim();
	if (query) fetchRecommendations(query);
});

document.getElementById("menuHome").onclick = () => showPage("home");
document.getElementById("menuFav").onclick = () => showPage("fav");
document.getElementById("goHome").onclick = () => showPage("home");

// 모달 기능 (기존 유지)
const imageModal = document.getElementById("imageModal");
const fullImage = document.getElementById("fullImage");
window.openModal = (src) => {
	fullImage.src = src;
	imageModal.style.display = "flex";
};

// ─────────────────────────────────────
// 빈 화면 랜덤 카피 문구 (기존 유지)
// ─────────────────────────────────────
const emptyCopies = ["오늘도 '아무거나'는 없습니다 🙅", "AI는 이미 맛집을 알고 있어요. 당신만 모를 뿐 🤫", "오늘 점심, 아직도 고민 중이세요? 🤔", "당신의 위장이 원하는 곳, AI가 찾아드려요 🤖", "검색 한 번으로 후회 없는 한 끼를 🍜", "맛집 고민에 쓰는 시간, 이제 AI한테 넘기세요 ⏱️", "오늘 뭐 먹지? 저한테 물어보세요 😎", "전국 맛집 데이터, 지금 당신을 기다리는 중 📍", "배는 고픈데 검색하기 귀찮다면? 저기요! 🙋", "좋은 식사는 좋은 하루를 만듭니다 ☀️", "AI가 추천하면 맛없으면 AI 탓이에요 😇", "오늘의 맛집, 운명처럼 찾아드릴게요 ✨", "혼밥도, 데이트도, 회식도 저기요가 해결해요 🍽️", "지금 이 순간에도 누군가는 맛집을 찾고 있어요 🔍", "맛집 탐험, 지금 시작해볼까요? 🗺️", "위치만 알려주세요, 나머지는 AI가 할게요 📌", "오늘 식사, 후회 없이 골라드릴게요 💯", "검색창에 동네 이름부터 입력해보세요 🏘️", "맛있는 건 참을 수 없잖아요 😋", "저기요, 거기 맛있어요? AI한테 물어봤어요 🤖"];

function showEmptyMessage() {
	const randomIndex = Math.floor(Math.random() * emptyCopies.length);
	const emptyMessage = document.getElementById("emptyMessage");
	const emptyCopy = emptyMessage.querySelector(".empty-copy");

	emptyCopy.textContent = emptyCopies[randomIndex];
	emptyMessage.style.display = "flex";
}

function hideEmptyMessage() {
	document.getElementById("emptyMessage").style.display = "none";
}

document.querySelector(".close-modal").onclick = () => (imageModal.style.display = "none");
showEmptyMessage();