// 1. 상태 관리
let favorites = JSON.parse(localStorage.getItem("jogiyo_favs")) || [];

// 2. DOM 요소
const restaurantList = document.getElementById("restaurantList");
const favList = document.getElementById("favList");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

// 3. API 호출 함수 (Vercel Python API 연동)
const fetchRecommendations = async (query) => {
	restaurantList.innerHTML = '<div class="loading">AI가 맛집을 찾고 있어요...</div>';

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
		restaurantList.innerHTML = '<div class="empty-msg">오류가 발생했습니다. 다시 시도해주세요.</div>';
	}
};

// 4. 카드 렌더링 함수
const renderCards = (data, targetElement) => {
	if (!data || data.length === 0) {
		targetElement.innerHTML = '<div class="empty-msg">검색 결과가 없습니다.</div>';
		return;
	}

	targetElement.innerHTML = data
		.map((store) => {
			const isFav = favorites.some((f) => f.id === store.id);
			return `
            <div class="card">
                <button class="fav-btn ${isFav ? "active" : ""}" onclick='toggleFavorite(${JSON.stringify(store)})'>
                    ${isFav ? "❤️" : "🤍"}
                </button>
                <div class="slider-container">
                    ${store.images.map((img) => `<img src="${img}" class="slider-img" onclick="openModal('${img}')">`).join("")}
                </div>
                <div class="card-info">
                    <h4>${store.name}</h4>
                    <p>${store.desc}</p>
                </div>
            </div>
        `;
		})
		.join("");
};

// 5. 즐겨찾기 토글 로직
window.toggleFavorite = (store) => {
	const index = favorites.findIndex((f) => f.id === store.id);
	if (index > -1) {
		favorites.splice(index, 1); // 해제
	} else {
		favorites.push(store); // 등록
	}
	localStorage.setItem("jogiyo_favs", JSON.stringify(favorites));

	// 현재 페이지 새로고침 (UI 업데이트)
	if (document.getElementById("favPage").style.display === "block") {
		renderCards(favorites, favList);
	} else {
		// 홈 화면이라면 하트 색상만 변경하기 위해 다시 렌더링하거나 클래스 토글 가능
		// 여기서는 간단히 전체 다시 렌더링(성능상 큰 문제 없음)
		const currentItems = Array.from(restaurantList.querySelectorAll(".card")).length;
		if (currentItems > 0) {
			// 현재 검색 결과가 있을 때만 유지 (실제로는 상태 변수에 저장해두는 것이 좋음)
		}
	}
	alert(index > -1 ? "즐겨찾기에서 삭제되었습니다." : "즐겨찾기에 추가되었습니다!");
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

// 7. 이벤트 리스너
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
// 빈 화면 랜덤 카피 문구
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
showEmptyMessage(); // 초기 로딩 시 빈 화면 메시지 표시
