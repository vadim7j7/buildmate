---
name: platform-check
description: Verify platform-specific code works correctly on both iOS and Android
---

# /platform-check -- Cross-Platform Verification

## What This Does

Scans the codebase for platform-specific code patterns and verifies that both
iOS and Android are properly handled. Identifies missing platform checks,
inconsistent behaviour, and platform-specific bugs.

## Usage

```
/platform-check                   # Check all source files
/platform-check app/              # Check only screen files
/platform-check components/       # Check only components
```

## How It Works

### 1. Scan for Platform-Specific Code

Search the codebase for platform-specific patterns:

```bash
# Find Platform.OS usage
grep -rn "Platform\.OS" app/ components/ hooks/ --include="*.tsx" --include="*.ts"

# Find Platform.select usage
grep -rn "Platform\.select" app/ components/ hooks/ --include="*.tsx" --include="*.ts"

# Find platform-specific file extensions
find . -name "*.ios.tsx" -o -name "*.android.tsx" | head -50

# Find SafeAreaView usage
grep -rn "SafeAreaView\|useSafeAreaInsets" app/ components/ --include="*.tsx"

# Find KeyboardAvoidingView without platform check
grep -rn "KeyboardAvoidingView" app/ components/ --include="*.tsx"

# Find shadow styles (different on iOS vs Android)
grep -rn "shadowColor\|shadowOffset\|elevation" app/ components/ constants/ --include="*.tsx" --include="*.ts"
```

### 2. Verify Platform Completeness

For each platform-specific pattern found, verify:

#### Screens with Primary Actions
- [ ] iOS screens have header bar buttons for primary actions
- [ ] Android screens have FAB or appropriate alternative
- [ ] Both platforms have the same set of available actions

#### Safe Area Handling
- [ ] Root screens use SafeAreaView or useSafeAreaInsets
- [ ] Correct edges are specified (not blocking tab bar or header)
- [ ] Modal screens handle all edges
- [ ] Landscape orientation considered if supported

#### Keyboard Handling
- [ ] Forms use KeyboardAvoidingView
- [ ] `behavior` prop is platform-specific (`'padding'` on iOS, `'height'` on Android)
- [ ] `keyboardVerticalOffset` accounts for navigation header on iOS
- [ ] `keyboardShouldPersistTaps="handled"` on ScrollViews inside forms

#### Shadows
- [ ] No direct `shadowColor`/`shadowOffset` without platform check
- [ ] Shadow constants from `constants/shadows.ts` are used
- [ ] Android uses `elevation` property
- [ ] iOS uses `shadowColor`, `shadowOffset`, `shadowOpacity`, `shadowRadius`

#### Navigation
- [ ] Android hardware back button handled for custom flows
- [ ] Modal dismiss works on both platforms (swipe down on iOS, back button on Android)
- [ ] Deep linking works on both platforms

#### Touch Feedback
- [ ] `Pressable` preferred over `TouchableOpacity`
- [ ] `android_ripple` set on Pressable components
- [ ] iOS pressed state provides visual feedback (opacity or scale)

### 3. Generate Report

```markdown
## Platform Check Report

### Summary
- **Files scanned:** N
- **Platform-specific patterns found:** N
- **Issues found:** N (X critical, Y warning)

### Critical Issues (Must Fix)
1. `app/(tabs)/items.tsx:45` - KeyboardAvoidingView missing platform-specific
   behavior prop. Currently hardcoded to 'padding' which breaks on Android.
2. `components/ui/Card.tsx:22` - Shadow styles use iOS-only properties without
   Android elevation fallback.

### Warnings
1. `app/(tabs)/dashboard.tsx` - No FAB on Android for the "add" action.
   iOS has a header button but Android has no equivalent.
2. `components/forms/SearchBar.tsx` - No android_ripple on Pressable.

### Platform Coverage Matrix

| Screen/Component | iOS Header Btn | Android FAB | SafeArea | Keyboard | Shadows |
|-----------------|----------------|-------------|----------|----------|---------|
| ItemsScreen     | Yes            | Yes         | Yes      | N/A      | N/A     |
| ItemFormScreen  | Yes (Save)     | Yes (Save)  | Yes      | Yes      | N/A     |
| Card            | N/A            | N/A         | N/A      | N/A      | Yes     |
| SearchBar       | N/A            | N/A         | N/A      | Yes      | N/A     |

### Recommendations
- <actionable suggestions for improving cross-platform consistency>
```

### 4. Write Pipeline Artefact

Write results to `.agent-pipeline/platform-check.md` if running as part of the
pipeline.

## Common Issues to Flag

### Missing Android Handling
- Screen has iOS header button but no Android FAB
- KeyboardAvoidingView uses `behavior="padding"` without platform check
- Shadow styles only include iOS properties

### Missing iOS Handling
- Android back handler without iOS gesture consideration
- Only `elevation` without iOS shadow properties

### Inconsistent Behaviour
- Different features available on different platforms
- Different navigation flows per platform (beyond expected UX differences)
- Different error handling per platform

### Missing Safe Area
- Content hidden behind notch or Dynamic Island
- Content hidden behind Android system navigation bar
- Bottom content hidden behind tab bar
